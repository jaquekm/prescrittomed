# PrescrittoMED

## Visão geral
Plataforma Django para gestão clínica com isolamento multi-tenant por hospital.

## Variáveis de ambiente
Defina as variáveis abaixo (ex.: arquivo `.env` carregado pelo serviço):

- `SECRET_KEY` (obrigatória)
- `DEBUG` (`True`/`False`)
- `ALLOWED_HOSTS` (lista CSV)
- `CSRF_TRUSTED_ORIGINS` (lista CSV, com URLs completas)
- `DATABASE_URL` (ex.: `postgres://...` ou `sqlite:///db.sqlite3`)
- `OPENAI_API_KEY` (se usar rascunhos de prescrição)

## Deploy (resumo)
1. Criar venv e instalar dependências:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Configurar variáveis de ambiente.
3. Rodar migrações:
   ```bash
   python manage.py migrate
   ```
4. Coletar arquivos estáticos:
   ```bash
   python manage.py collectstatic --noinput
   ```
5. Subir o servidor (ex.: gunicorn) apontando para `hospital_system.wsgi`.

## Checklist de release
- [ ] `python manage.py check --deploy`
- [ ] `python manage.py makemigrations --check --dry-run`
- [ ] `python manage.py migrate`
- [ ] `python manage.py verify_tenant_isolation`
- [ ] `python manage.py test`
- [ ] `python manage.py collectstatic --noinput` (staging/produção)
- [ ] Reiniciar serviços (gunicorn/nginx)

## CI
O pipeline de CI em `.github/workflows/ci.yml` executa:
- install deps
- `check --deploy`
- `migrate`
- `verify_tenant_isolation`
- `test`
- `collectstatic` (staging)

## Comando de smoke test multi-tenant
Execute:
```bash
python manage.py verify_tenant_isolation
```
O comando cria dois hospitais, um médico por hospital e valida que não há acesso cruzado.
