"""
api — Capa REST para Método Base.

Expone los servicios del core como endpoints HTTP/JSON,
permitiendo que clientes web y móviles consuman la misma
lógica de negocio que usa la aplicación de escritorio.

Uso de desarrollo:
    uvicorn api.main:app --reload

Documentación interactiva:
    http://localhost:8000/docs      (Swagger UI)
    http://localhost:8000/redoc     (ReDoc)
"""
