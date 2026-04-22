from __future__ import annotations

import pandas as pd

from pnt_supervisor.core.enums import FixType
from pnt_supervisor.parsers.xlsx_mapper import XLSXMapper


def test_xlsx_mapper_maps_expected_columns_and_extras(tmp_path) -> None:
    df = pd.DataFrame(
        [
            {
                "timestamp": 100.0,
                "GPS_0_Lat": 10.1,
                "GPS_0_Lng": 20.2,
                "GPS_0_Alt": 33.3,
                "GPS_0_Spd": 4.4,
                "GPS_0_GCrs": 55.5,
                "GPS_0_VZ": -0.5,
                "GPS_0_Status": 6,
                "GPS_0_NSats": 15,
                "GPS_0_HDop": 0.6,
                "GPA_0_HAcc": 0.7,
                "GPA_0_VAcc": 0.9,
                "BARO_Alt": 31.0,
                "MAG_Heading": 54.0,
                "XKF1_Lat": 10.09,
                "XKF1_Lon": 20.19,
                "XKF1_Alt": 32.9,
                "XKF1_Spd": 4.5,
                "UNMAPPED": "keep-me",
            }
        ]
    )
    path = tmp_path / "synthetic.xlsx"
    df.to_excel(path, index=False)

    mapper = XLSXMapper()
    observations = list(mapper.from_file(path))
    assert len(observations) == 1
    obs = observations[0]

    assert obs.fix_type == FixType.RTK_FIXED
    assert obs.fix_valid is True
    assert obs.baro_alt_m == 31.0
    assert obs.ekf_lat_deg == 10.09
    assert obs.extras["UNMAPPED"] == "keep-me"


def test_xlsx_mapper_missing_optional_columns_does_not_crash(tmp_path) -> None:
    df = pd.DataFrame(
        [
            {
                "timestamp": 1.0,
                "GPS_0_Lat": 1.1,
                "GPS_0_Lng": 2.2,
                "GPS_0_Alt": 3.3,
                "GPS_0_Spd": 4.4,
                "GPS_0_GCrs": 5.5,
                "GPS_0_VZ": 0.1,
                "GPS_0_Status": 3,
                "GPS_0_NSats": 7,
                "GPS_0_HDop": 1.2,
                "GPA_0_HAcc": 0.8,
                "GPA_0_VAcc": 1.1,
            }
        ]
    )
    path = tmp_path / "minimal.xlsx"
    df.to_excel(path, index=False)

    mapper = XLSXMapper()
    observations = list(mapper.from_file(path))

    assert len(observations) == 1
    assert observations[0].fix_type == FixType.FIX_3D
    assert observations[0].baro_alt_m is None
    assert observations[0].mag_heading_deg is None
