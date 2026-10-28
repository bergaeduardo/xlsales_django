# xlsales_django

Migración de XLSales (subsistemas **Arreglos** + **CADS**) de ASP.NET WebForms + EF6 a Django.

## Alcance

| Subsistema | Estado |
|---|---|
| Arreglos (A1–A6) | En migración |
| CADS — Devoluciones (D1–D7) | En migración |
| Compartidos (C1–C4) | En migración |
| Sales | ❌ Fuera de alcance |

## Stack

- Python 3.11 / Django 5.0
- PostgreSQL (`default`) — auth, sesiones, PerfilUsuario
- SQL Server (`xlsales`) — datos existentes de XLSales (managed=False)
- SQL Server readonly (`tango`) — ERP Tango, validación NC
- UI: Tabler

## Setup local

```bash
cp .env.example .env
# Editar .env con las credenciales locales
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e ".[dev]"
python manage.py migrate
python manage.py runserver
```

## Docs clave

- Plan Maestro: AFFiNE doc `o6PLsH5tqd`
- Relevamiento de módulos: AFFiNE doc `vv2VWyVBKI`
- Anti-patterns a evitar: `XLSales/ANALISIS_ERRORES_MIGRACION.md`
- Playbook base: proyecto `ubicaciones_django`
