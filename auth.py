from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import crud
import os
from dotenv import load_dotenv # <--- 1. Import nécessaire
from database import get_db

# <--- 2. Chargement du fichier .env
load_dotenv()

# <--- 3. Récupération des variables sécurisées
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256") # Valeur par défaut "HS256" si non trouvé
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)) # Conversion en int() obligatoire !

# Sécurité : On vérifie que la clé secrète existe bien
if not SECRET_KEY:
    raise ValueError("❌ Erreur critique : La variable SECRET_KEY est absente du fichier .env")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Fonctions utilitaires
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db: Session, telephone: str, password: str):
    utilisateur = crud.get_utilisateur_by_telephone(db, telephone)
    if not utilisateur:
        return False
    if not verify_password(password, utilisateur.mot_de_passe):
        return False
    return utilisateur

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES) # Utilise la variable convertie
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Dépendances d'authentification
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        telephone: str = payload.get("sub")
        if telephone is None:
            raise credentials_exception
        token_data = {"telephone": telephone}
    except JWTError:
        raise credentials_exception
    utilisateur = crud.get_utilisateur_by_telephone(db, telephone=telephone)
    if utilisateur is None:
        raise credentials_exception
    return utilisateur

async def get_current_active_user(current_user = Depends(get_current_user)):
    return current_user

# Vérification des rôles
def require_role(role: str):
    def role_checker(current_user = Depends(get_current_user)):
        if current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"L'accès nécessite le rôle {role}"
            )
        return current_user
    return role_checker

def require_role_admin_tresorier(current_user = Depends(get_current_user)):
    if current_user.role not in ["admin", "trésorier"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="L'accès nécessite un rôle admin ou trésorier"
        )
    return current_user