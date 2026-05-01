from __future__ import annotations

import pandas as pd

from pnt_supervisor.adapters import ArduPilotLogCSVAdapter


def test_csv_adapter_reads_rows_and_extras(tmp_path) -> None:
    df = pd.DataFrame(
        [
            {
                "timestamp": 10.0,
                "GPS_0_Lat": 1.0,
                "GPS_0_Lng": 2.0,
                "GPS_0_Alt": 3.0,
                "GPS_0_Spd": 4.0,
                "GPS_0_GCrs": 90.0,
                "GPS_0_VZ": 0.1,
                "GPS_0_Status": 3,
                "GPS_0_NSats": 8,
                "GPS_0_HDop": 0.9,
                "GPA_0_HAcc": 0.7,
                "GPA_0_VAcc": 1.1,
                "IMU_AccX": 0.0,
                "IMU_AccY": 0.0,
                "IMU_AccZ": 9.81,
            }
        ]
    )
    path = tmp_path / "log.csv"
    df.to_csv(path, index=False)

    adapter = ArduPilotLogCSVAdapter(path)
    observations = list(adapter.iter_observations())

    assert len(observations) == 1
    assert observations[0].speed_mps == 4.0
    assert observations[0].extras["IMU_AccZ"] == 9.81
