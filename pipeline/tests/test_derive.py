import numpy as np, pandas as pd
import pytest
from olp.derive import derive, RMV

INC = ["inc_main_annual", "inc_main_inkind", "inc_self_annual", "inc_self_autoconsumo",
       "inc_sec_annual", "inc_sec_inkind", "inc_sec_self", "inc_sec_autoconsumo", "inc_extra_annual"]
BASE = {"year": 2023, "ocu500": 1, "age": 30, "ocupinf_inei": 2, "emplpsec_inei": 2, "sunat_reg": 1, "books": 1,
        "ins_essalud": 1, "ins_eps": 2, "ins_priv": 2, "ins_ffaa": 2, "ins_sis": 2, "ins_univ": 2, "ins_other1": 2, "ins_other": 2,
        "pension_none": 1, "contract": 1, "cat_ocup": 3, "cat_ocup_sec": np.nan, "firm_size": 2, "ciiu4": 4711,
        "hours_lastweek_main": 40, "hours_sec": 8, "hours_usual": np.nan, "hours_usual_raw": np.nan, "normal_hours": 1,
        "wants_more": 2, "avail_more": 2, "attends": np.nan, "dept": "15", "prov": "1501",
        "pobreza": 3, "ciuo": 5223, "res5_same": 1, "res5_ubigeo": np.nan, "birth_same": 1, "birth_ubigeo": np.nan, **{c: 0.0 for c in INC}}


def people(*overrides):
    return derive(pd.DataFrame([{**BASE, **o} for o in overrides]))


def test_labour_force_flags():
    d = people({"ocu500": 1}, {"ocu500": 2}, {"ocu500": 3}, {"ocu500": 4})
    assert d.pea.tolist() == [1, 1, 0, 0]          # desocupado oculto (3) queda fuera de la PEA
    assert d.ocupado.tolist() == [1, 0, 0, 0] and d.desocupado.tolist() == [0, 1, 0, 0]
    assert d.informal.isna().tolist() == [False, True, True, True]   # sólo definido para ocupados


def test_informal_uses_inei_flag_when_present_and_rule_otherwise():
    d = people({"ocupinf_inei": 1}, {"ocupinf_inei": 2})
    assert d.informal.tolist() == [1, 0] and d.informal_source.iloc[0] == "inei"
    # sin ocupinf (como 2024): asalariado sin contrato → informal; con EsSalud, pensión y contrato → formal
    d = people({"ocupinf_inei": np.nan, "emplpsec_inei": np.nan, "contract": 7}, {"ocupinf_inei": np.nan, "emplpsec_inei": np.nan})
    assert d.informal.tolist() == [1, 0] and d.informal_source.iloc[0] == "rule"


def test_hours_use_last_week_when_normal_else_usual():
    d = people({}, {"normal_hours": 2, "hours_usual": 20}, {"normal_hours": 2, "hours_usual_raw": 60})
    assert d.hours.tolist() == [48, 20, 60]
    assert d.hours_lt35.tolist() == [0, 1, 0] and d.hours_ge60.tolist() == [0, 0, 1]


def test_income_is_sum_of_components_over_12_and_underemployment():
    low, high = RMV[2023] * 12 - 12, RMV[2023] * 12
    d = people({"inc_main_annual": 6000, "inc_main_inkind": 1200, "inc_extra_annual": 1200},
               {"inc_main_annual": low}, {"inc_main_annual": high},
               {"inc_main_annual": low, "hours_lastweek_main": 20, "hours_sec": 0, "wants_more": 1, "avail_more": 1})
    assert d.inc_month_nom.iloc[0] == 700
    assert d.subemp_income.tolist()[1:] == [1, 0, 0]   # el subempleo por horas tiene prioridad
    assert d.subemp_hours.tolist() == [0, 0, 0, 1]
    assert d.adecuado.tolist() == [0, 0, 1, 0]
    assert (d.inc_month_real >= d.inc_month_nom).all()  # deflactor a soles de 2024


def test_neet_only_for_youth_not_working_not_attending():
    d = people({"age": 20, "ocu500": 4}, {"age": 20, "ocu500": 4, "attends": 1}, {"age": 20, "ocu500": 1}, {"age": 40, "ocu500": 4})
    assert d.neet.iloc[:3].tolist() == [1, 0, 0] and pd.isna(d.neet.iloc[3])


def test_migration_and_lima_split():
    d = people({}, {"res5_same": 2, "res5_ubigeo": 80101}, {"res5_same": 2, "res5_ubigeo": 150201}, {"dept": "07", "prov": "0701"}, {"prov": "1502"})
    assert d.mig_5y.tolist() == [0, 1, 0, 0, 0] and d.mig2.tolist()[:2] == [1, 2]
    assert d.lima.tolist() == ["15M", "15M", "15M", "15M", "15R"]


def test_hidden_unemployment_extends_the_labour_force():
    d = people({"ocu500": 1}, {"ocu500": 2}, {"ocu500": 3}, {"ocu500": 4})
    assert d.desocupado_oculto.tolist() == [0, 0, 1, 0]
    assert d.desocupado_ext.tolist() == [0, 1, 1, 0] and d.pea_ext.tolist() == [1, 1, 1, 0]


def test_working_poor_insurance_type_and_occupation_group():
    d = people({"pobreza": 1}, {"pobreza": 2}, {"pobreza": 3, "ins_essalud": 2, "ins_sis": 1, "ciuo": 111}, {"ocu500": 4, "pobreza": 1})
    assert d.working_poor.iloc[:3].tolist() == [1, 1, 0] and pd.isna(d.working_poor.iloc[3])   # sólo ocupados
    assert d.seguro_contrib.iloc[:3].tolist() == [1, 1, 0] and d.sis.iloc[:3].tolist() == [0, 0, 1]
    assert d.ocup10.iloc[:3].tolist() == [5, 5, 0] and pd.isna(d.ocup10.iloc[3])


def test_hourly_income_divides_monthly_by_monthly_hours():
    d = people({"inc_main_annual": 12 * 2080, "hours_lastweek_main": 40, "hours_sec": 0})
    assert d.inc_hour_real.iloc[0] == pytest.approx(d.inc_month_real.iloc[0] / (40 * 52 / 12))
