import pytest

def calculate_carbon_equivalent(c, mn, cr, mo, v, ni, cu):
    # CE = C + Mn/6 + (Cr+Mo+V)/5 + (Ni+Cu)/15
    return c + (mn / 6.0) + ((cr + mo + v) / 5.0) + ((ni + cu) / 15.0)

def test_ce_calculation_for_known_compositions():
    ce = calculate_carbon_equivalent(0.15, 1.2, 0.5, 0.2, 0.1, 0.3, 0.3)
    # 0.15 + 0.2 + 0.16 + 0.04 = 0.55
    assert pytest.approx(ce, 0.01) == 0.55

def test_weldability_classification():
    ce = 0.55
    if ce > 0.45:
        weldability = "POOR"
    elif ce > 0.35:
        weldability = "FAIR"
    else:
        weldability = "GOOD"
    assert weldability == "POOR"

def test_astm_validation():
    material = "A106 GR.B"
    assert "A106" in material
