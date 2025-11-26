"""Seed system config data with common values

Revision ID: 004
Revises: 003
Create Date: 2025-11-26 16:00:00.000000

"""
from typing import Sequence, Union
from datetime import datetime
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed system configuration tables with common values."""

    now = datetime.utcnow()

    # Seed Hardware
    hardware_data = [
        {'id': str(uuid4()), 'name': 'Raspberry Pi', 'description': 'Single-board computer series', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'Arduino', 'description': 'Microcontroller boards', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'ESP32', 'description': 'Low-cost microcontroller with Wi-Fi and Bluetooth', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'ESP8266', 'description': 'Low-cost Wi-Fi microchip', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'Custom PCB', 'description': 'Custom printed circuit board', 'created_at': now, 'updated_at': now},
    ]
    op.bulk_insert(
        sa.table('hardware',
                 sa.column('id', sa.String),
                 sa.column('name', sa.String),
                 sa.column('description', sa.Text),
                 sa.column('created_at', sa.DateTime),
                 sa.column('updated_at', sa.DateTime)),
        hardware_data
    )

    # Seed Datatypes
    datatype_data = [
        {'id': str(uuid4()), 'name': 'Temperature', 'description': 'Temperature measurements in Celsius or Fahrenheit', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'Humidity', 'description': 'Relative humidity percentage', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'Pressure', 'description': 'Atmospheric pressure measurements', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'Light', 'description': 'Light intensity or luminosity', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'Motion', 'description': 'Motion detection or movement', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'Sound', 'description': 'Sound level or noise measurements', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'Gas', 'description': 'Gas concentration measurements', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'Voltage', 'description': 'Electrical voltage', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'Current', 'description': 'Electrical current', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'Boolean', 'description': 'True/False or On/Off state', 'created_at': now, 'updated_at': now},
    ]
    op.bulk_insert(
        sa.table('datatypes',
                 sa.column('id', sa.String),
                 sa.column('name', sa.String),
                 sa.column('description', sa.Text),
                 sa.column('created_at', sa.DateTime),
                 sa.column('updated_at', sa.DateTime)),
        datatype_data
    )

    # Seed Protocols
    protocol_data = [
        {'id': str(uuid4()), 'name': 'MQTT', 'description': 'Message Queuing Telemetry Transport', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'HTTP', 'description': 'Hypertext Transfer Protocol', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'HTTPS', 'description': 'HTTP Secure', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'CoAP', 'description': 'Constrained Application Protocol', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'WebSocket', 'description': 'Full-duplex communication protocol', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'Modbus', 'description': 'Serial communication protocol', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'LoRaWAN', 'description': 'Long Range Wide Area Network', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'Zigbee', 'description': 'Low-power mesh networking', 'created_at': now, 'updated_at': now},
    ]
    op.bulk_insert(
        sa.table('protocols',
                 sa.column('id', sa.String),
                 sa.column('name', sa.String),
                 sa.column('description', sa.Text),
                 sa.column('created_at', sa.DateTime),
                 sa.column('updated_at', sa.DateTime)),
        protocol_data
    )

    # Seed Parsers
    parser_data = [
        {'id': str(uuid4()), 'name': 'JSON', 'description': 'JavaScript Object Notation parser', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'XML', 'description': 'Extensible Markup Language parser', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'CSV', 'description': 'Comma-Separated Values parser', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'Binary', 'description': 'Binary data parser', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'Plain Text', 'description': 'Plain text parser', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'Custom', 'description': 'Custom parsing logic', 'created_at': now, 'updated_at': now},
    ]
    op.bulk_insert(
        sa.table('parsers',
                 sa.column('id', sa.String),
                 sa.column('name', sa.String),
                 sa.column('description', sa.Text),
                 sa.column('created_at', sa.DateTime),
                 sa.column('updated_at', sa.DateTime)),
        parser_data
    )

    # Seed Manufacturers
    manufacturer_data = [
        {'id': str(uuid4()), 'name': 'Raspberry Pi Foundation', 'description': 'Makers of Raspberry Pi boards', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'Arduino', 'description': 'Arduino hardware manufacturer', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'Espressif Systems', 'description': 'Manufacturer of ESP32 and ESP8266', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'Bosch', 'description': 'Sensor and electronics manufacturer', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'Texas Instruments', 'description': 'Semiconductor manufacturer', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'STMicroelectronics', 'description': 'Electronics and semiconductor manufacturer', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'Generic', 'description': 'Generic or unknown manufacturer', 'created_at': now, 'updated_at': now},
    ]
    op.bulk_insert(
        sa.table('manufacturers',
                 sa.column('id', sa.String),
                 sa.column('name', sa.String),
                 sa.column('description', sa.Text),
                 sa.column('created_at', sa.DateTime),
                 sa.column('updated_at', sa.DateTime)),
        manufacturer_data
    )

    # Seed Communication Modes
    communication_mode_data = [
        {'id': str(uuid4()), 'name': 'Wi-Fi', 'description': 'Wireless network communication', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'Ethernet', 'description': 'Wired network communication', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'Bluetooth', 'description': 'Short-range wireless communication', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'LoRa', 'description': 'Long-range low-power wireless', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'Cellular', 'description': 'Mobile network communication', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'Serial', 'description': 'Serial port communication', 'created_at': now, 'updated_at': now},
        {'id': str(uuid4()), 'name': 'USB', 'description': 'Universal Serial Bus', 'created_at': now, 'updated_at': now},
    ]
    op.bulk_insert(
        sa.table('communication_modes',
                 sa.column('id', sa.String),
                 sa.column('name', sa.String),
                 sa.column('description', sa.Text),
                 sa.column('created_at', sa.DateTime),
                 sa.column('updated_at', sa.DateTime)),
        communication_mode_data
    )


def downgrade() -> None:
    """Remove seed data from system configuration tables."""
    # Delete seed data in reverse order
    op.execute("DELETE FROM communication_modes")
    op.execute("DELETE FROM manufacturers")
    op.execute("DELETE FROM parsers")
    op.execute("DELETE FROM protocols")
    op.execute("DELETE FROM datatypes")
    op.execute("DELETE FROM hardware")
