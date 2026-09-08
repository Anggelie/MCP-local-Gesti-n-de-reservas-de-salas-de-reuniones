"""Reglas de negocio y persistencia JSON para las reservas."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"

INITIAL_ROOMS = [
    {
        "room_id": "room-001",
        "name": "Sala Atitlán",
        "capacity": 12,
        "location": "Edificio A, segundo nivel",
        "features": ["pantalla", "videoconferencia", "pizarra"],
    },
    {
        "room_id": "room-002",
        "name": "Sala Pacífico",
        "capacity": 8,
        "location": "Edificio A, primer nivel",
        "features": ["pantalla", "pizarra"],
    },
    {
        "room_id": "room-003",
        "name": "Sala Maya",
        "capacity": 20,
        "location": "Edificio B, tercer nivel",
        "features": ["pantalla", "videoconferencia", "pizarra", "micrófonos"],
    },
]


class ReservationError(ValueError):
    """Error controlado de una operación de reservas."""


class ReservationService:
    """Administra salas y reservas usando archivos JSON locales."""

    def __init__(self, rooms_file: Path, reservations_file: Path) -> None:
        self._rooms_file = rooms_file
        self._reservations_file = reservations_file
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        self._rooms_file.parent.mkdir(parents=True, exist_ok=True)
        if not self._rooms_file.exists():
            self._save(self._rooms_file, INITIAL_ROOMS)
        if not self._reservations_file.exists():
            self._save(self._reservations_file, [])

    def list_rooms(self) -> list[dict[str, Any]]:
        """Devuelve todas las salas configuradas."""
        return self._load(self._rooms_file)

    def check_availability(
        self, room_id: str, date: str, start_time: str, end_time: str
    ) -> dict[str, Any]:
        """Comprueba si una sala está libre durante un intervalo."""
        self._validate_interval(date, start_time, end_time)
        self._get_room(room_id)
        reservations = self._load(self._reservations_file)
        available = not any(
            self._overlaps(reservation, room_id, date, start_time, end_time)
            for reservation in reservations
        )
        return {
            "room_id": room_id,
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "available": available,
        }

    def create_reservation(
        self,
        room_id: str,
        date: str,
        start_time: str,
        end_time: str,
        reserved_by: str,
        title: str,
    ) -> dict[str, Any]:
        """Crea una reserva si la sala y el intervalo son válidos."""
        self._validate_interval(date, start_time, end_time)
        self._get_room(room_id)
        if not reserved_by.strip() or not title.strip():
            raise ReservationError("reserved_by y title no pueden estar vacíos.")

        reservations = self._load(self._reservations_file)
        if any(
            self._overlaps(reservation, room_id, date, start_time, end_time)
            for reservation in reservations
        ):
            raise ReservationError("La sala ya está reservada durante ese intervalo.")

        reservation = {
            "reservation_id": self._next_reservation_id(reservations),
            "room_id": room_id,
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "reserved_by": reserved_by.strip(),
            "title": title.strip(),
        }
        reservations.append(reservation)
        self._save(self._reservations_file, reservations)
        return reservation

    def cancel_reservation(self, reservation_id: str) -> dict[str, Any]:
        """Cancela una reserva existente y devuelve el registro cancelado."""
        reservations = self._load(self._reservations_file)
        for index, reservation in enumerate(reservations):
            if reservation.get("reservation_id") == reservation_id:
                cancelled = reservations.pop(index)
                self._save(self._reservations_file, reservations)
                return cancelled
        raise ReservationError(f"No existe la reserva '{reservation_id}'.")

    def list_reservations(
        self, date: str | None = None, room_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Lista reservas y aplica filtros opcionales por fecha o sala."""
        if date is not None:
            self._validate_date(date)
        reservations = self._load(self._reservations_file)
        return [
            reservation
            for reservation in reservations
            if (date is None or reservation.get("date") == date)
            and (room_id is None or reservation.get("room_id") == room_id)
        ]

    def _get_room(self, room_id: str) -> dict[str, Any]:
        for room in self.list_rooms():
            if room.get("room_id") == room_id:
                return room
        raise ReservationError(f"No existe la sala '{room_id}'.")

    @staticmethod
    def _validate_date(date_text: str) -> None:
        try:
            parsed_date = datetime.strptime(date_text, DATE_FORMAT).date()
        except ValueError as error:
            raise ReservationError("date debe tener el formato YYYY-MM-DD.") from error

        if parsed_date < datetime.now().date():
            raise ReservationError("La fecha no puede ser una fecha pasada. Debe ser hoy o una fecha futura.")

    @classmethod
    def _validate_interval(cls, date: str, start_time: str, end_time: str) -> None:
        cls._validate_date(date)
        try:
            start = datetime.strptime(start_time, TIME_FORMAT)
            end = datetime.strptime(end_time, TIME_FORMAT)
        except ValueError as error:
            raise ReservationError("Las horas deben tener el formato HH:MM.") from error

        if datetime.strptime(date, DATE_FORMAT).date() == datetime.now().date() and start.time() < datetime.now().time():
            raise ReservationError("La hora no puede ser una hora pasada.")
        if start >= end:
            raise ReservationError("La hora de inicio debe ser menor que la hora final.")

    @classmethod
    def _overlaps(
        cls,
        reservation: dict[str, Any],
        room_id: str,
        date: str,
        start_time: str,
        end_time: str,
    ) -> bool:
        if reservation.get("room_id") != room_id or reservation.get("date") != date:
            return False
        current_start = datetime.strptime(start_time, TIME_FORMAT)
        current_end = datetime.strptime(end_time, TIME_FORMAT)
        reserved_start = datetime.strptime(reservation["start_time"], TIME_FORMAT)
        reserved_end = datetime.strptime(reservation["end_time"], TIME_FORMAT)
        return current_start < reserved_end and current_end > reserved_start

    @staticmethod
    def _next_reservation_id(reservations: list[dict[str, Any]]) -> str:
        used_ids = {
            reservation.get("reservation_id")
            for reservation in reservations
            if isinstance(reservation.get("reservation_id"), str)
        }
        number = 1
        while f"RES-{number:04d}" in used_ids:
            number += 1
        return f"RES-{number:04d}"

    @staticmethod
    def _load(path: Path) -> list[dict[str, Any]]:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            raise ReservationError(f"El archivo {path.name} debe contener una lista de objetos.")
        return data

    @staticmethod
    def _save(path: Path, data: list[dict[str, Any]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = path.with_suffix(f"{path.suffix}.tmp")
        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")
        temporary_path.replace(path)