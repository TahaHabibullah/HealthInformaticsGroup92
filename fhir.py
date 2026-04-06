import json
from storage import find_one, safe_write

def build_patient_resource(customer):
    return {
        "resourceType": "Patient",
        "id": customer["customer_id"],
        "name": [
            {
                "text": customer["name"]
            }
        ]
    }

def build_encounter_resource(encounter):
    return {
        "resourceType": "Encounter",
        "id": encounter["encounter_id"],
        "status": "finished",
        "subject": {
            "reference": f"Patient/{encounter['customer_id']}"
        }
    }

def build_observation_resource(encounter_id, symptoms_text):
    return {
        "resourceType": "Observation",
        "id": f"{encounter_id}-symptoms",
        "status": "final",
        "code": {
            "text": "Reported symptoms"
        },
        "subject": {
            "reference": f"Patient/{encounter_id}"
        },
        "valueString": symptoms_text
    }

def build_diagnostic_report_resource(encounter_id, ai_results_text):
    return {
        "resourceType": "DiagnosticReport",
        "id": f"{encounter_id}-report",
        "status": "final",
        "code": {
            "text": "AI Similar Case Report"
        },
        "subject": {
            "reference": f"Patient/{encounter_id}"
        },
        "conclusion": ai_results_text
    }

def save_fhir_resource(encounter_id, resource):
    safe_write("fhir", [
        encounter_id,
        resource["resourceType"],
        json.dumps(resource)
    ])

def generate_fhir_resources_for_encounter(encounter_id):
    encounter = find_one("encounters", "encounter_id", encounter_id)
    if encounter is None:
        raise ValueError("Encounter not found")

    customer = find_one("customers", "customer_id", encounter["customer_id"])
    if customer is None:
        raise ValueError("Customer not found")

    symptom_row = find_one("symptoms", "encounter_id", encounter_id)
    ai_row = find_one("ai", "encounter_id", encounter_id)

    symptoms_text = symptom_row["symptoms"] if symptom_row else ""
    ai_results_text = ai_row["results"] if ai_row else ""

    patient_resource = build_patient_resource(customer)
    encounter_resource = build_encounter_resource(encounter)
    observation_resource = build_observation_resource(encounter_id, symptoms_text)
    diagnostic_report_resource = build_diagnostic_report_resource(encounter_id, ai_results_text)

    resources = [
        patient_resource,
        encounter_resource,
        observation_resource,
        diagnostic_report_resource
    ]

    for resource in resources:
        save_fhir_resource(encounter_id, resource)

    return resources

def build_fhir_bundle(resources):
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [{"resource": resource} for resource in resources]
    }