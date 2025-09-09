"""
Auto-generated indicator definitions from Sotkanet API.
Generated: 2025-09-09T13:55:21.463722
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
    5051: {
        'id': 5051,
        'name_fi': 'Lonkkamurtumapotilaiden 365 päivän kuolleisuus, vakioitu %',
        'name_sv': 'Dödlighet inom 365 dagar för patienter med höftledsfraktur, standardiserad %',
        'name_en': '365-day mortality in hip fracture patients, adjusted %',
        'unit': '%',
        'organization': 'Terveyden ja hyvinvoinnin laitos (THL)',
        'decimals': 1,
        'last_updated': '2025-04-03'
    },
    5074: {
        'id': 5074,
        'name_fi': 'Kirurgisen ja muun lääketieteellisen hoidon komplikaatiot, % hoitojaksoista',
        'name_sv': 'Komplikationer vid kirurgisk eller annan medicinsk behandling, % av behandlingsperioderna',
        'name_en': 'Complications in surgical and other medical care, % of admissions',
        'unit': '%',
        'organization': 'Terveyden ja hyvinvoinnin laitos (THL)',
        'decimals': 1,
        'last_updated': '2025-05-07'
    },
    5034: {
        'id': 5034,
        'name_fi': 'Lonkan kokotekonivelen ensileikkaukset / 100 000 asukasta',
        'name_sv': 'Primära operationer av total höftledsprotes / 100 000 invånare',
        'name_en': 'Primary surgeries for total hip replacement per 100,000 inhabitants',
        'unit': '/ 100 000',
        'organization': 'Terveyden ja hyvinvoinnin laitos (THL)',
        'decimals': 1,
        'last_updated': '2025-05-14'
    },
    5033: {
        'id': 5033,
        'name_fi': 'Erikoissairaanhoitoon saapuneet yli 21 vrk:ssa käsitellyt lähetteet, % saapuneista lähetteistä ',
        'name_sv': 'Antalet remisser som inkommit till den specialiserade sjukvården efter mer än 21 dagars behandling, % av inkomna remisser',
        'name_en': 'Referrals for specialised health care received after processing for more than 21 days, % of the referrals received ',
        'unit': '%',
        'organization': 'Terveyden ja hyvinvoinnin laitos (THL)',
        'decimals': 0,
        'last_updated': '2025-02-17'
    },
    3336: {
        'id': 3336,
        'name_fi': 'Erikoissairaanhoitoa yli 6 kk odottaneet vuoden aikana / 10 000 asukasta ',
        'name_sv': 'Antalet personer som väntat på specialiserad sjukvård under året i mer än 6 månader / 10 000 invånare ',
        'name_en': 'Patients waiting over 6 months during the year for access to specialised health care per 10 000 inhabitants',
        'unit': '/ 10 000',
        'organization': 'Terveyden ja hyvinvoinnin laitos (THL)',
        'decimals': 1,
        'last_updated': '2025-04-10'
    },
}

# Helper functions
def get_indicator_by_id(indicator_id):
    """Get indicator metadata by ID."""
    return INDICATORS.get(indicator_id, {})

def get_all_ids():
    """Get list of all indicator IDs."""
    return list(INDICATORS.keys())