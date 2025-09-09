"""
Auto-generated indicator definitions from Sotkanet API.
Generated: 2025-09-09T11:01:04.289645
"""

INDICATORS = {
    186: {
        'id': 186,
        'name_fi': 'Kuolleisuus / 100 000 asukasta',
        'name_sv': 'Dödlighet / 100 000 invånare',
        'name_en': 'Mortality per 100 000 inhabitants',
        'unit': '/ 100 000',
        'organization': 'Tilastokeskus',
        'decimals': 1,
        'last_updated': '2025-04-29'
    },
    322: {
        'id': 322,
        'name_fi': 'Kuolleisuus 65 vuotta täyttäneillä / 100 000 vastaavan ikäistä',
        'name_sv': 'Dödlighet i åldrarna 65 år och över / 100 000 i samma åldrar',
        'name_en': 'Mortality among population aged 65 and over per 100 000 persons of same age',
        'unit': '/ 100 000',
        'organization': 'Tilastokeskus',
        'decimals': 0,
        'last_updated': '2025-04-29'
    },
    5527: {
        'id': 5527,
        'name_fi': 'Terveysliikuntasuosituksen mukaan liian vähän liikkuvien osuus (%)',
        'name_sv': 'Andelen personer (%) som motionerar för lite enligt rekommendationen om hälsomotion',
        'name_en': 'According to the recommendation on physical activity, the share of those with insufficient physical activity (%)',
        'unit': '%',
        'organization': 'Terveyden ja hyvinvoinnin laitos (THL)',
        'decimals': 1,
        'last_updated': '2025-05-14'
    },
    5529: {
        'id': 5529,
        'name_fi': 'Terveysliikuntasuosituksen mukaan liian vähän liikkuvien osuus (%), 65 vuotta täyttäneet',
        'name_sv': 'Andelen personer (%) som motionerar för lite enligt rekommendationen om hälsomotion, 65 år och äldre',
        'name_en': 'According to the recommendation on physical activity, the share of those with insufficient physical activity (%), age 65 and over',
        'unit': '%',
        'organization': 'Terveyden ja hyvinvoinnin laitos (THL)',
        'decimals': 1,
        'last_updated': '2025-05-14'
    },
    4559: {
        'id': 4559,
        'name_fi': 'Terveydelle suotuisat elintavat (%), 20 - 69-vuotiaat',
        'name_sv': 'Hälsosamma levnadsvanor (%), 20 - 69-åringar',
        'name_en': 'Health promoting behaviors (%), age 20-69',
        'unit': '%',
        'organization': 'Terveyden ja hyvinvoinnin laitos (THL)',
        'decimals': 1,
        'last_updated': '2025-05-30'
    },
    4461: {
        'id': 4461,
        'name_fi': 'Lihavien osuus (kehon painoindeksi BMI ≥ 30 kg/m2) (%), 65 vuotta täyttäneet',
        'name_sv': 'Andelen feta personer (kroppsmasseindex BMI ≥ 30 kg/m2) (%), 65 år och äldre',
        'name_en': 'Obesity (Body Mass Index BMI ≥ 30 kg/m2) (%), age 65 and over',
        'unit': '%',
        'organization': 'Terveyden ja hyvinvoinnin laitos (THL)',
        'decimals': 1,
        'last_updated': '2025-05-14'
    },
}

# Helper functions
def get_indicator_by_id(indicator_id):
    """Get indicator metadata by ID."""
    return INDICATORS.get(indicator_id, {})

def get_all_ids():
    """Get list of all indicator IDs."""
    return list(INDICATORS.keys())