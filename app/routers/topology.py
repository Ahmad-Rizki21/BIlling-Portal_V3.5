from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.data_teknis import DataTeknis as DataTeknisModel
from ..models.odp import ODP as ODPModel
from ..models.olt import OLT as OLTModel
from ..models.pelanggan import Pelanggan as PelangganModel
from ..schemas.topology import TopologyNode

router = APIRouter(
    prefix="/topology",
    tags=["Topology"],
    responses={404: {"description": "Not found"}},
)


@router.get("/olt/{olt_id}", response_model=TopologyNode)
async def get_olt_topology(olt_id: int, db: AsyncSession = Depends(get_db)):
    """
    Mengambil data hierarki topologi untuk satu OLT.
    """
    # 1. Ambil data OLT beserta semua relasi di bawahnya (ODP -> DataTeknis -> Pelanggan)
    olt = await db.get(
        OLTModel,
        olt_id,
        options=[
            selectinload(OLTModel.mikrotik_server),
            selectinload(OLTModel.odps).selectinload(ODPModel.data_teknis).selectinload(DataTeknisModel.pelanggan),
        ],
    )

    if not olt:
        raise HTTPException(status_code=404, detail="OLT tidak ditemukan")

    # 2. Susun data menjadi struktur pohon (tree)

    # Root Node (Mikrotik)
    mikrotik_node = TopologyNode(
        name=olt.mikrotik_server.name if olt.mikrotik_server else "Unknown Mikrotik",
        type="Mikrotik",
        ip=olt.mikrotik_server.host_ip if olt.mikrotik_server else None,
    )

    # Level 1 (OLT)
    olt_node = TopologyNode(
        name=olt.nama_olt,
        type="OLT",
        ip=olt.ip_address,
        status="active",  # Anda bisa kembangkan logika status ini
    )

    # Level 2 (ODP) dan Level 3 (Pelanggan)
    for odp in olt.odps:
        kapasitas_str = f"{len(odp.data_teknis)}/{odp.kapasitas_port}"
        odp_node = TopologyNode(name=odp.kode_odp, type="ODP", kapasitas=kapasitas_str, children=[])

        for dt in odp.data_teknis:
            if dt.pelanggan:
                pelanggan_node = TopologyNode(
                    name=dt.pelanggan.nama,
                    type="Pelanggan",
                    ip=dt.ip_pelanggan,
                    status="active",  # Ambil dari status langganan jika perlu
                )
                odp_node.children.append(pelanggan_node)

        olt_node.children.append(odp_node)

    mikrotik_node.children.append(olt_node)

    return mikrotik_node
