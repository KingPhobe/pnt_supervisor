from __future__ import annotations

import pandas as pd

from pnt_supervisor.adapters import ArduPilotExcelObservationAdapter
from pnt_supervisor.core.models import EpochObservation


def test_ardupilot_excel_adapter_maps_fields_and_defaults(tmp_path) -> None:
    df = pd.DataFrame(
        [
            {
                "GPS_0_TimeUS": 2_000_000,
                "GPS_0_Lat": 37.5,
                "GPS_0_Lng": -122.3,
                "GPS_0_Status": 3,
            },
            {
                "GPS_0_TimeUS": 1_000_000,
                "GPS_0_Lat": 37.4,
                "GPS_0_Lng": -122.2,
                "GPS_0_Status": 2,
            },
            {
                "GPS_0_TimeUS": 3_000_000,
                "GPS_0_Lat": None,
                "GPS_0_Lng": -122.4,
                "GPS_0_Status": 4,
            },
        ]
    )
    path = tmp_path / "input.xlsx"
    df.to_excel(path, sheet_name="in", index=False)

    adapter = ArduPilotExcelObservationAdapter(path, sheet_name="in")
    observations = list(adapter.iter_observations())

    assert len(observations) == 2
    assert all(isinstance(obs, EpochObservation) for obs in observations)

    assert observations[0].t_sec == 1.0
    assert observations[1].t_sec == 2.0

    assert observations[1].fix_valid is True
    assert observations[0].fix_valid is False

    assert observations[0].hdop == 99.0
    assert observations[0].num_sats == 0
    assert observations[0].speed_mps == 0.0
    assert observations[0].course_deg == 0.0
    assert observations[0].climb_mps == 0.0
