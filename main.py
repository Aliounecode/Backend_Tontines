from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import crud, models, schemas
from database import engine, get_db
from datetime import date, timedelta
from auth import (
    authenticate_user, create_access_token, 
    get_current_user, get_current_active_user,
    require_role, require_role_admin_tresorier,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Gestion Tontine", version="1.0.0")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:4201"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- AUTHENTIFICATION ---

@app.post("/login", response_model=schemas.Token)
async def login(user: schemas.UtilisateurLogin, db: Session = Depends(get_db)):
    utilisateur = authenticate_user(db, user.telephone, user.mot_de_passe)
    if not utilisateur:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Téléphone ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": utilisateur.telephone, "role": utilisateur.role},
        expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "utilisateur": utilisateur
    }

@app.get("/profil", response_model=schemas.Utilisateur)
async def lire_profil(current_user = Depends(get_current_active_user)):
    return current_user

# --- UTILISATEURS ---

@app.post("/utilisateurs", response_model=schemas.Utilisateur)
def creer_utilisateur(utilisateur: schemas.UtilisateurCreate, db: Session = Depends(get_db)):
    # Vérification doublons
    if crud.get_utilisateur_by_telephone(db, telephone=utilisateur.telephone):
        raise HTTPException(status_code=400, detail="Téléphone déjà enregistré")
    if crud.get_utilisateur_by_email(db, email=utilisateur.email):
        raise HTTPException(status_code=400, detail="Email déjà enregistré")
    return crud.create_utilisateur(db=db, utilisateur=utilisateur)

@app.get("/utilisateurs", response_model=List[schemas.Utilisateur])
def lire_utilisateurs(
    skip: int = 0, limit: int = 100, 
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin")) # Seul l'admin voit tout le monde
):
    return crud.get_utilisateurs(db, skip=skip, limit=limit)

@app.get("/utilisateurs/{utilisateur_id}", response_model=schemas.Utilisateur)
def lire_utilisateur(utilisateur_id: int, db: Session = Depends(get_db)):
    db_utilisateur = crud.get_utilisateur(db, utilisateur_id=utilisateur_id)
    if db_utilisateur is None:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return db_utilisateur

@app.delete("/utilisateurs/{utilisateur_id}")
def supprimer_utilisateur(
    utilisateur_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin")) # Seul l'admin peut supprimer
):
    success = crud.delete_utilisateur(db, utilisateur_id)
    if not success:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return {"message": "Utilisateur supprimé"}

# --- TONTINES ---

@app.post("/tontines", response_model=schemas.Tontine)
def creer_tontine(
    tontine: schemas.TontineCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(require_role_admin_tresorier) # Sécurisé
):
    # On utilise l'ID de l'utilisateur connecté comme trésorier
    return crud.create_tontine(db=db, tontine=tontine, tresorier_id=current_user.id)

@app.get("/tontines", response_model=List[schemas.Tontine])
def lire_tontines(
    skip: int = 0, limit: int = 100, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Si Admin ou Trésorier, voit tout, sinon logic à adapter si besoin
    # Pour l'instant on laisse voir la liste publique des tontines
    return crud.get_tontines(db, skip=skip, limit=limit)

@app.get("/tontines/mes-tontines", response_model=List[schemas.Tontine])
def lire_mes_tontines(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role == "membre":
        # Récupérer les tontines où l'utilisateur est membre
        membres = crud.get_membres_by_utilisateur(db, current_user.id)
        tontines_ids = [m.id_tontine for m in membres]
        return crud.get_tontines_by_ids(db, tontines_ids)
    
    # Si trésorier, voir celles qu'il gère
    if current_user.role == "trésorier":
        return crud.get_tontines_by_tresorier(db, current_user.id)
        
    # Admin voit tout
    return crud.get_tontines(db)

@app.get("/tontines/{tontine_id}", response_model=schemas.Tontine)
def lire_tontine(tontine_id: int, db: Session = Depends(get_db)):
    db_tontine = crud.get_tontine(db, tontine_id=tontine_id)
    if db_tontine is None:
        raise HTTPException(status_code=404, detail="Tontine non trouvée")
    return db_tontine

@app.put("/tontines/{tontine_id}", response_model=schemas.Tontine)
def modifier_tontine(
    tontine_id: int, 
    tontine: schemas.TontineCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(require_role_admin_tresorier)
):
    return crud.update_tontine(db, tontine_id, tontine)

@app.delete("/tontines/{tontine_id}")
def supprimer_tontine(
    tontine_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    success = crud.delete_tontine(db, tontine_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tontine non trouvée")
    return {"message": "Tontine supprimée"}

@app.get("/tontines/{tontine_id}/statistiques")
def lire_statistiques_tontine(tontine_id: int, db: Session = Depends(get_db)):
    return crud.get_statistiques_tontine(db, tontine_id=tontine_id)

# --- MEMBRES ---

@app.post("/tontines/{tontine_id}/rejoindre")
def rejoindre_tontine(
    tontine_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Vérifications...
    tontine = crud.get_tontine(db, tontine_id)
    if not tontine:
        raise HTTPException(status_code=404, detail="Tontine non trouvée")
    
    existing = crud.get_membre_by_user_tontine(db, current_user.id, tontine_id)
    if existing:
        raise HTTPException(status_code=400, detail="Vous êtes déjà membre")
    
    nb_membres = crud.count_membres_tontine(db, tontine_id)
    if nb_membres >= tontine.nombre_max_membres:
         raise HTTPException(status_code=400, detail="Tontine complète")

    membre_data = schemas.MembreCreate(
        id_tontine=tontine_id,
        id_utilisateur=current_user.id,
        position=nb_membres + 1,
        date_adhesion=date.today()
    )
    return crud.add_membre(db, membre_data)

@app.post("/membres", response_model=schemas.Membre)
def ajouter_membre_manuel(
    membre: schemas.MembreCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(require_role_admin_tresorier) # Réservé aux gestionnaires
):
    # Logique d'ajout manuel par un trésorier
    return crud.add_membre(db=db, membre=membre)

@app.get("/tontines/{tontine_id}/membres", response_model=List[schemas.Membre])
def lire_membres_tontine(tontine_id: int, db: Session = Depends(get_db)):
    return crud.get_membres_by_tontine(db, tontine_id=tontine_id)

@app.delete("/membres/{membre_id}")
def retirer_membre(
    membre_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(require_role_admin_tresorier)
):
    success = crud.remove_membre(db, membre_id)
    if not success:
        raise HTTPException(status_code=404, detail="Membre non trouvé")
    return {"message": "Membre retiré de la tontine"}

# --- PAIEMENTS & TOURS ---

@app.post("/paiements", response_model=schemas.Paiement)
def effectuer_paiement(
    paiement: schemas.PaiementCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # On force l'ID utilisateur avec celui connecté (sécurité)
    return crud.create_paiement(db=db, paiement=paiement, utilisateur_id=current_user.id)

@app.get("/tontines/{tontine_id}/paiements", response_model=List[schemas.Paiement])
def lire_paiements_tontine(tontine_id: int, db: Session = Depends(get_db)):
    return crud.get_paiements_by_tontine(db, tontine_id=tontine_id)

@app.post("/tours", response_model=schemas.Tour)
def creer_tour(
    tour: schemas.TourCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(require_role_admin_tresorier)
):
    return crud.create_tour(db=db, tour=tour)

@app.get("/tontines/{tontine_id}/tours", response_model=List[schemas.Tour])
def lire_tours_tontine(tontine_id: int, db: Session = Depends(get_db)):
    return crud.get_tours_by_tontine(db, tontine_id=tontine_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)