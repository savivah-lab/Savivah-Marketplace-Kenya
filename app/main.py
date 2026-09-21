import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from models.base import Base
from core.db import engine
# from core.config import settings
from routers import auth, admin_auth, products, stores, checkout, payments, orders, webhooks, admin
from workers.payout_sweep import run_sweep_job
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("savivah.main")
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail fast and loud on missing critical config — same discipline as the
    # previous Node implementation, just enforced by pydantic-settings at
    # import time instead (see core/config.py: DATABASE_URL, JWT_SECRET,
    # ADMIN_JWT_SECRET are required fields with no default, so the app
    # simply won't start without them).
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables created/verified")
    scheduler.add_job(run_sweep_job, "interval", minutes=15, id="payout_sweep")
    scheduler.start()
    logger.info("Savivah API starting — payout sweep scheduled every 15 minutes")
    yield
    scheduler.shutdown()


app = FastAPI(title="Savivah API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin_auth.router)
app.include_router(products.router)
app.include_router(stores.router)
app.include_router(checkout.router)
app.include_router(payments.router)
app.include_router(orders.router)
app.include_router(webhooks.router)
app.include_router(admin.router)

@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    return {"The api is running fine": True}


@app.get("/health")
async def health():
    return {"status": "ok"}

