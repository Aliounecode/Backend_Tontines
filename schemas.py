from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional

# --- Schémas Utilisateur ---
class UtilisateurBase(BaseModel):
    nom_utilisateur: str
    telephone: str
    email: EmailStr
    role: str = "membre"

class UtilisateurCreate(UtilisateurBase):
    mot_de_passe: str

class Utilisateur(UtilisateurBase):
    id: int
    date_creation: datetime
    
    class Config:
        from_attributes = True

class UtilisateurLogin(BaseModel):
    telephone: str
    mot_de_passe: str

# --- Schémas Tontine ---
class TontineBase(BaseModel):
    nom: str
    description: Optional[str] = None
    montant_cotisation: int
    frequence: str
    mode_rotation: str
    nombre_max_membres: int
    date_demarrage: date

class TontineCreate(TontineBase):
    pass

class Tontine(TontineBase):
    id: int
    id_tresorier: int
    date_creation: datetime
    
    class Config:
        from_attributes = True

# --- Schémas Membre ---
class MembreBase(BaseModel):
    id_tontine: int
    id_utilisateur: int
    position: int

class MembreCreate(MembreBase):
    date_adhesion: date

class Membre(MembreBase):
    id: int
    date_adhesion: date
    
    class Config:
        from_attributes = True

# --- Schémas Paiement ---
class PaiementBase(BaseModel):
    id_tontine: int
    montant: int
    periode: int

class PaiementCreate(PaiementBase):
    pass

class Paiement(PaiementBase):
    id: int
    id_utilisateur: int
    date_versement: datetime
    
    class Config:
        from_attributes = True

# --- Schémas Tour ---
class TourBase(BaseModel):
    id_tontine: int
    periode: int
    montant_recu: int

class TourCreate(TourBase):
    id_utilisateur: int

class Tour(TourBase):
    id: int
    id_utilisateur: int
    date_reception: datetime
    
    class Config:
        from_attributes = True

# --- Statistiques ---
class StatistiquesTontine(BaseModel):
    total_cotisations: int
    total_distribue: int
    solde_restant: int
    membres_actifs: int
    tours_realises: int

# --- Authentification ---
class Token(BaseModel):
    access_token: str
    token_type: str
    utilisateur: Utilisateur

class TokenData(BaseModel):
    telephone: Optional[str] = None
    role: Optional[str] = None