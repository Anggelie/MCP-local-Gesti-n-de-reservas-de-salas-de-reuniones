"""Pruebas de las reglas de negocio de reservas."""

import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from src.reservation_service import ReservationError, ReservationService


class ReservationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        rooms_file = root / "rooms.json"
        reservations_file = root / "reservations.json"
        rooms_file.write_text(json.dumps([{ "room_id": "room-001", "name": "Sala Atitlán" }], ensure_ascii=False), encoding="utf-8")
        reservations_file.write_text("[]", encoding="utf-8")
        self.service = ReservationService(rooms_file, reservations_file)

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_crea_reserva_y_detecta_superposicion(self) -> None:
        reservation = self.service.create_reservation(
            "room-001", "2026-09-15", "10:00", "11:00", "Anggelie", "Reunión"
        )

        self.assertEqual(reservation["reservation_id"], "RES-0001")
        with self.assertRaisesRegex(ReservationError, "superpuesta|reservada"):
            self.service.create_reservation(
                "room-001", "2026-09-15", "10:30", "11:30", "Anggelie", "Otra reunión"
            )

    def test_hora_inicial_menor_que_hora_final(self) -> None:
        with self.assertRaisesRegex(ReservationError, "menor"):
            self.service.check_availability("room-001", "2026-09-15", "11:00", "10:00")

    def test_rechaza_fecha_pasada(self) -> None:
        past_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        with self.assertRaisesRegex(ReservationError, "no puede ser una fecha pasada|fecha pasada"):
            self.service.create_reservation(
                "room-001", past_date, "09:00", "10:00", "Anggelie", "Reunión pasada"
            )

    def test_cancela_reserva_inexistente(self) -> None:
        with self.assertRaisesRegex(ReservationError, "No existe"):
            self.service.cancel_reservation("RES-9999")

    def test_crea_archivos_iniciales_en_directorio_vacio(self) -> None:
        root = Path(self.directory.name) / "empty-data"
        service = ReservationService(root / "rooms.json", root / "reservations.json")

        self.assertEqual(len(service.list_rooms()), 3)
        self.assertEqual(service.list_reservations(), [])
        self.assertTrue((root / "rooms.json").is_file())
        self.assertTrue((root / "reservations.json").is_file())


if __name__ == "__main__":
    unittest.main()