from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from model import chain
import os
import uuid

from storage import init_csv, safe_write, find_all, read_all
from rag import ClinicalRetrieval
from fhir import generate_fhir_resources_for_encounter, build_fhir_bundle
from request import EncounterRequest, SymptomRequest, FHIRRequest

app = FastAPI()
frontend_url = os.getenv("FRONTEND_URL")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

retriever = ClinicalRetrieval()

init_csv()

try:
    retriever.load_index()
except FileNotFoundError:
    print("embeddings.pkl not found. Run rag.py first.")

@app.get("/")
def serve_frontend():
    return FileResponse(os.path.join("frontend", "index.html"))

@app.get("/data-viewer")
def serve_data_viewer():
    return FileResponse(os.path.join("frontend", "data_viewer.html"))

@app.post("/customers")
def create_customer():
    customer_id = str(uuid.uuid4())
    safe_write("customers", [customer_id])
    return {"customer_id": customer_id}

@app.post("/encounters")
def create_encounter(req: EncounterRequest):
    customer_id_exists = any(
        row["customer_id"] == req.customer_id for row in read_all("customers")
    )

    if not customer_id_exists:
        raise HTTPException(status_code=404, detail="Customer not found")

    encounter_id = str(uuid.uuid4())
    safe_write("encounters", [encounter_id, req.customer_id])
    return {"encounter_id": encounter_id}

@app.post("/symptoms")
def submit_symptoms(req: SymptomRequest):
    encounter_exists = any(
        row["encounter_id"] == req.encounter_id for row in read_all("encounters")
    )

    if not encounter_exists:
        raise HTTPException(status_code=404, detail="Encounter not found")

    safe_write("symptoms", [req.encounter_id, req.symptoms])

    try:
        results = retriever.query(req.symptoms)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")

    response = chain.invoke({"symptoms": req.symptoms, "documents": str(results)})
    safe_write("ai", [req.encounter_id, str(response)])

    return response

@app.post("/encounters/fhir")
def export_fhir_bundle(req: FHIRRequest):
    try:
        resources = generate_fhir_resources_for_encounter(req)
        bundle = build_fhir_bundle(resources)
        return bundle
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FHIR export failed: {str(e)}")

@app.get("/encounters/{encounter_id}/fhir/resources")
def get_saved_fhir_resources(encounter_id: str):
    rows = find_all("fhir", "encounter_id", encounter_id)
    if not rows:
        raise HTTPException(status_code=404, detail="No FHIR resources found for this encounter")
    return {"resources": rows}

@app.get("/data/customers")
def get_customers_data():
    return {"rows": read_all("customers")}

@app.get("/data/encounters")
def get_encounters_data():
    return {"rows": read_all("encounters")}

@app.get("/data/symptoms")
def get_symptoms_data():
    return {"rows": read_all("symptoms")}

@app.get("/data/ai")
def get_ai_data():
    return {"rows": read_all("ai")}

@app.get("/data/fhir")
def get_fhir_data():
    return {"rows": read_all("fhir")}