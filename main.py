from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import crud, models, schemas
from database import engine, get_db
from datetime import date

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Gestion Tontine", version="1.0.0")

# Configuration CORS
# C'est parfait ici, on autorise bien Angular
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:4201"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variable pour simuler l'utilisateur connecté (à remplacer par système d'authentification)
current_user_id = 1

# --- ROUTES UTILISATEURS (Slashs retirés) ---
@app.post("/utilisateurs", response_model=schemas.Utilisateur)
def creer_utilisateur(utilisateur: schemas.UtilisateurCreate, db: Session = Depends(get_db)):
    db_utilisateur = crud.get_utilisateur_by_telephone(db, telephone=utilisateur.telephone)
    if db_utilisateur:
        raise HTTPException(status_code=400, detail="Téléphone déjà enregistré")
    db_utilisateur = crud.get_utilisateur_by_email(db, email=utilisateur.email)
    if db_utilisateur:
        raise HTTPException(status_code=400, detail="Email déjà enregistré")
    return crud.create_utilisateur(db=db, utilisateur=utilisateur)

@app.get("/utilisateurs", response_model=List[schemas.Utilisateur])
def lire_utilisateurs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    utilisateurs = crud.get_utilisateurs(db, skip=skip, limit=limit)
    return utilisateurs

@app.get("/utilisateurs/{utilisateur_id}", response_model=schemas.Utilisateur)
def lire_utilisateur(utilisateur_id: int, db: Session = Depends(get_db)):
    db_utilisateur = crud.get_utilisateur(db, utilisateur_id=utilisateur_id)
    if db_utilisateur is None:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return db_utilisateur

@app.delete("/utilisateurs/{utilisateur_id}")
def supprimer_utilisateur(utilisateur_id: int, db: Session = Depends(get_db)):
    success = crud.delete_utilisateur(db, utilisateur_id)
    if not success:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return {"message": "Utilisateur supprimé"}

# --- ROUTES TONTINES (Slashs retirés) ---
@app.post("/tontines", response_model=schemas.Tontine)
def creer_tontine(tontine: schemas.TontineCreate, db: Session = Depends(get_db)):
    return crud.create_tontine(db=db, tontine=tontine, tresorier_id=current_user_id)

@app.get("/tontines", response_model=List[schemas.Tontine])
def lire_tontines(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tontines = crud.get_tontines(db, skip=skip, limit=limit)
    return tontines

@app.get("/tontines/mes-tontines", response_model=List[schemas.Tontine])
def lire_mes_tontines(db: Session = Depends(get_db)):
    tontines = crud.get_tontines_by_tresorier(db, tresorier_id=current_user_id)
    return tontines

@app.get("/tontines/{tontine_id}", response_model=schemas.Tontine)
def lire_tontine(tontine_id: int, db: Session = Depends(get_db)):
    db_tontine = crud.get_tontine(db, tontine_id=tontine_id)
    if db_tontine is None:
        raise HTTPException(status_code=404, detail="Tontine non trouvée")
    return db_tontine

@app.get("/tontines/{tontine_id}/statistiques")
def lire_statistiques_tontine(tontine_id: int, db: Session = Depends(get_db)):
    return crud.get_statistiques_tontine(db, tontine_id=tontine_id)

@app.delete("/tontines/{tontine_id}")
def supprimer_tontine(tontine_id: int, db: Session = Depends(get_db)):
    success = crud.delete_tontine(db, tontine_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tontine non trouvée")
    return {"message": "Tontine supprimée"}

@app.put("/tontines/{tontine_id}", response_model=schemas.Tontine)
def modifier_tontine(tontine_id: int, tontine: schemas.TontineCreate, db: Session = Depends(get_db)):
    return crud.update_tontine(db, tontine_id, tontine)

# --- ROUTES MEMBRES (Slashs retirés) ---
@app.post("/membres", response_model=schemas.Membre)
def ajouter_membre(membre: schemas.MembreCreate, db: Session = Depends(get_db)):
    # Vérifier si la tontine existe
    tontine = crud.get_tontine(db, membre.id_tontine)
    if not tontine:
        raise HTTPException(status_code=404, detail="Tontine non trouvée")
    
    # Vérifier si l'utilisateur existe
    utilisateur = crud.get_utilisateur(db, membre.id_utilisateur)
    if not utilisateur:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Vérifier si l'utilisateur est déjà membre
    existing = crud.get_membre_by_user_tontine(db, membre.id_utilisateur, membre.id_tontine)
    if existing:
        raise HTTPException(status_code=400, detail="Utilisateur déjà membre de cette tontine")
    
    # Vérifier le nombre maximum de membres
    nombre_membres = crud.count_membres_tontine(db, membre.id_tontine)
    if nombre_membres >= tontine.nombre_max_membres:
        raise HTTPException(status_code=400, detail="Nombre maximum de membres atteint")
    
    return crud.add_membre(db=db, membre=membre)

@app.get("/tontines/{tontine_id}/membres", response_model=List[schemas.Membre])
def lire_membres_tontine(tontine_id: int, db: Session = Depends(get_db)):
    membres = crud.get_membres_by_tontine(db, tontine_id=tontine_id)
    return membres

@app.delete("/membres/{membre_id}")
def retirer_membre(membre_id: int, db: Session = Depends(get_db)):
    success = crud.remove_membre(db, membre_id)
    if not success:
        raise HTTPException(status_code=404, detail="Membre non trouvé")
    return {"message": "Membre retiré de la tontine"}

# --- ROUTES PAIEMENTS (Slashs retirés) ---
@app.post("/paiements", response_model=schemas.Paiement)
def effectuer_paiement(paiement: schemas.PaiementCreate, db: Session = Depends(get_db)):
    # Vérifier si la tontine existe
    tontine = crud.get_tontine(db, paiement.id_tontine)
    if not tontine:
        raise HTTPException(status_code=404, detail="Tontine non trouvée")
    
    # Vérifier si l'utilisateur est membre de la tontine
    membre = crud.get_membre_by_user_tontine(db, current_user_id, paiement.id_tontine)
    if not membre:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas membre de cette tontine")
    
    return crud.create_paiement(db=db, paiement=paiement, utilisateur_id=current_user_id)

@app.get("/tontines/{tontine_id}/paiements", response_model=List[schemas.Paiement])
def lire_paiements_tontine(tontine_id: int, db: Session = Depends(get_db)):
    paiements = crud.get_paiements_by_tontine(db, tontine_id=tontine_id)
    return paiements

# --- ROUTES TOURS (Slashs retirés) ---
@app.post("/tours", response_model=schemas.Tour)
def creer_tour(tour: schemas.TourCreate, db: Session = Depends(get_db)):
    # Vérifier si la tontine existe
    tontine = crud.get_tontine(db, tour.id_tontine)
    if not tontine:
        raise HTTPException(status_code=404, detail="Tontine non trouvée")
    
    # Vérifier si l'utilisateur est membre de la tontine
    membre = crud.get_membre_by_user_tontine(db, tour.id_utilisateur, tour.id_tontine)
    if not membre:
        raise HTTPException(status_code=403, detail="Utilisateur n'est pas membre de cette tontine")
    
    return crud.create_tour(db=db, tour=tour)

@app.get("/tontines/{tontine_id}/tours", response_model=List[schemas.Tour])
def lire_tours_tontine(tontine_id: int, db: Session = Depends(get_db)):
    tours = crud.get_tours_by_tontine(db, tontine_id=tontine_id)
    return tours

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)