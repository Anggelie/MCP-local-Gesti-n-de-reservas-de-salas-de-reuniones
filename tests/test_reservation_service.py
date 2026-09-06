"""Pruebas de las reglas de negocio de reservas."""

import json
import tempfile
import unittest
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

    def test_cancela_reserva_inexistente(self) -> None:
        with self.assertRaisesRegex(ReservationError, "No existe"):
            self.service.cancel_reservation("RES-9999")


if __name__ == "__main__":
    unittest.main()