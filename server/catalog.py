"""Fixed vocabularies: plant parts, observations, species profiles, conditions and suggestions.

Models only ever pick codes from these lists. Every user-facing word comes from here.
"""

from __future__ import annotations

from dataclasses import dataclass

PARTS: tuple[str, ...] = ("leaf", "stem", "soil", "roots")

PART_LABELS: dict[str, str] = {
    "leaf": "Folhas",
    "stem": "Caule",
    "soil": "Terra",
    "roots": "Raízes",
}

OBSERVATIONS: dict[str, tuple[str, str]] = {
    "leaf_healthy": ("leaf", "Folhas com cor e textura normais"),
    "leaf_yellow_lower": ("leaf", "Folhas de baixo amareladas"),
    "leaf_yellow_spread": ("leaf", "Amarelado espalhado pela planta"),
    "leaf_pale": ("leaf", "Verde mais claro que o normal da espécie"),
    "leaf_dark_dull": ("leaf", "Verde escuro e sem brilho"),
    "leaf_brown_tips": ("leaf", "Pontas ou bordas marrons e secas"),
    "leaf_scorch": ("leaf", "Manchas claras ou queimadas na parte exposta ao sol"),
    "leaf_spots_halo": ("leaf", "Manchas com borda amarelada ou anel"),
    "leaf_powdery": ("leaf", "Pó branco sobre as folhas"),
    "leaf_soft_dark": ("leaf", "Partes escuras e moles"),
    "leaf_drooping": ("leaf", "Folhas caídas ou murchas"),
    "leaf_curling": ("leaf", "Folhas enroladas ou encolhidas"),
    "leaf_small_new": ("leaf", "Folhas novas pequenas"),
    "leaf_pests": ("leaf", "Insetos, pontinhos ou teias finas"),
    "stem_healthy": ("stem", "Caule firme"),
    "stem_leggy": ("stem", "Caule esticado, com muito espaço entre as folhas"),
    "stem_leaning": ("stem", "Planta inclinada para um lado"),
    "stem_soft_base": ("stem", "Base do caule escura ou mole"),
    "stem_pests": ("stem", "Insetos ou bolinhas brancas no caule"),
    "soil_ok": ("soil", "Terra com aparência normal"),
    "soil_wet": ("soil", "Terra encharcada ou brilhando de água"),
    "soil_dry": ("soil", "Terra muito seca ou rachada"),
    "soil_pulling_away": ("soil", "Terra descolando da borda do vaso"),
    "soil_white_mold": ("soil", "Mofo branco na superfície da terra"),
    "soil_compacted": ("soil", "Terra dura e compactada"),
    "soil_roots_surfacing": ("soil", "Raízes aparecendo na superfície"),
    "roots_healthy": ("roots", "Raízes claras e firmes"),
    "roots_brown_mushy": ("roots", "Raízes marrons e moles"),
    "roots_circling": ("roots", "Raízes dando voltas no vaso"),
    "roots_dry": ("roots", "Raízes secas e quebradiças"),
}

LIGHT_LABELS: dict[str, str] = {
    "low": "Tolera pouca luz, mas cresce mais com luz indireta",
    "medium": "Luz indireta média, perto de uma janela sem sol direto",
    "bright_indirect": "Muita luz indireta; um pouco de sol fraco da manhã ajuda",
    "direct": "Sol direto por várias horas por dia",
}

WATER_LABELS: dict[str, str] = {
    "low": "Regue pouco: só quando a terra estiver seca por inteiro",
    "medium": "Regue quando os primeiros 2–3 cm da terra estiverem secos",
    "high": "Mantenha a terra levemente úmida, nunca encharcada",
}

HUMIDITY_LABELS: dict[str, str] = {
    "low": "Ar seco não é problema",
    "medium": "Umidade comum de casa serve",
    "high": "Gosta de ar úmido; agrupe com outras plantas ou use bandeja com pedrinhas e água",
}


@dataclass(frozen=True)
class SpeciesProfile:
    common_name: str
    scientific_name: str
    light: str
    water: str
    humidity: str
    growth_tip: str


SPECIES: dict[str, SpeciesProfile] = {
    "monstera_deliciosa": SpeciesProfile(
        "Costela-de-adão", "Monstera deliciosa", "bright_indirect", "medium", "high",
        "Um tutor de fibra ou musgo para ela escalar deixa as folhas maiores e mais recortadas.",
    ),
    "epipremnum_aureum": SpeciesProfile(
        "Jiboia", "Epipremnum aureum", "medium", "medium", "medium",
        "Podar as pontas compridas estimula brotos novos e deixa a planta mais cheia.",
    ),
    "spathiphyllum": SpeciesProfile(
        "Lírio-da-paz", "Spathiphyllum wallisii", "medium", "high", "high",
        "Mais luz indireta é o que mais ajuda a florescer.",
    ),
    "dracaena_trifasciata": SpeciesProfile(
        "Espada-de-são-jorge", "Dracaena trifasciata", "low", "low", "low",
        "Cresce devagar; mais luz e vaso de barro aceleram sem risco de encharcar.",
    ),
    "zamioculcas_zamiifolia": SpeciesProfile(
        "Zamioculca", "Zamioculcas zamiifolia", "low", "low", "low",
        "Excesso de rega é o maior risco; prefira regar de menos.",
    ),
    "chlorophytum_comosum": SpeciesProfile(
        "Clorofito", "Chlorophytum comosum", "medium", "medium", "medium",
        "As mudinhas que pendem podem ir para vasos novos e viram plantas novas.",
    ),
    "nephrolepis_exaltata": SpeciesProfile(
        "Samambaia", "Nephrolepis exaltata", "medium", "high", "high",
        "Ar úmido é o segredo; borrifar não substitui umidade constante.",
    ),
    "ficus_lyrata": SpeciesProfile(
        "Figueira-lira", "Ficus lyrata", "bright_indirect", "medium", "medium",
        "Não gosta de mudar de lugar; escolha um ponto claro e deixe lá.",
    ),
    "ficus_elastica": SpeciesProfile(
        "Falsa-seringueira", "Ficus elastica", "bright_indirect", "medium", "medium",
        "Limpar a poeira das folhas com pano úmido melhora a fotossíntese.",
    ),
    "calathea": SpeciesProfile(
        "Calateia", "Goeppertia spp.", "medium", "high", "high",
        "Água filtrada ou descansada evita pontas marrons.",
    ),
    "aloe_vera": SpeciesProfile(
        "Babosa", "Aloe vera", "direct", "low", "low",
        "Vaso de barro com terra arenosa evita apodrecer a base.",
    ),
    "succulent": SpeciesProfile(
        "Suculenta", "Crassulaceae", "direct", "low", "low",
        "Sol direto pela manhã mantém a planta compacta e com cor viva.",
    ),
    "cactus": SpeciesProfile(
        "Cacto", "Cactaceae", "direct", "low", "low",
        "No inverno, regue bem menos: é o período de descanso.",
    ),
}


@dataclass(frozen=True)
class Condition:
    label: str
    explanation: str
    suggestions: tuple[str, ...]


CONDITIONS: dict[str, Condition] = {
    "overwatering": Condition(
        "Excesso de água",
        "Os sinais indicam terra úmida por tempo demais, o que sufoca as raízes.",
        (
            "Espere a terra secar antes de regar de novo",
            "Confira se o vaso tem furos de drenagem",
            "Tire a água parada do pratinho",
        ),
    ),
    "underwatering": Condition(
        "Falta de água",
        "Os sinais indicam que a planta está passando sede.",
        (
            "Regue devagar até a água escorrer pela drenagem",
            "Se a terra descolou do vaso, mergulhe o vaso num balde por 10 minutos",
            "Observe a terra nos próximos dias para acertar a frequência",
        ),
    ),
    "low_light": Condition(
        "Pouca luz",
        "A planta parece estar se esticando atrás de luz.",
        (
            "Aproxime de uma janela clara, aos poucos",
            "Gire o vaso a cada semana para crescer por igual",
        ),
    ),
    "too_much_sun": Condition(
        "Sol demais",
        "Há sinais de queimadura nas partes mais expostas.",
        (
            "Afaste do sol direto da tarde",
            "Sol atrás do vidro também queima; use uma cortina leve",
        ),
    ),
    "low_humidity": Condition(
        "Ar seco",
        "Pontas secas costumam aparecer quando o ar está seco para a espécie.",
        (
            "Agrupe com outras plantas",
            "Use uma bandeja com pedrinhas e água embaixo do vaso",
            "Afaste de ar-condicionado e aquecedor",
        ),
    ),
    "fungus": Condition(
        "Possível fungo",
        "Há manchas ou pó com aparência de fungo comum.",
        (
            "Retire as folhas mais atingidas e jogue no lixo",
            "Evite molhar as folhas ao regar",
            "Melhore a ventilação do lugar",
        ),
    ),
    "pest": Condition(
        "Possível praga",
        "Há sinais de insetos comuns de plantas de casa.",
        (
            "Olhe o verso das folhas e os brotos novos",
            "Limpe as folhas com pano úmido",
            "Separe das outras plantas enquanto observa",
        ),
    ),
    "root_rot_risk": Condition(
        "Risco de apodrecer a raiz",
        "Base mole ou raízes escuras costumam vir de encharcamento prolongado.",
        (
            "Pare de regar até a terra secar",
            "Se puder, tire do vaso e corte as raízes moles com tesoura limpa",
            "Replante em terra nova e bem drenada",
        ),
    ),
    "pot_bound": Condition(
        "Vaso apertado",
        "As raízes parecem sem espaço para crescer.",
        (
            "Troque por um vaso 2 a 4 cm maior",
            "Faça a troca na primavera ou no verão",
        ),
    ),
    "poor_soil": Condition(
        "Terra cansada",
        "Terra compactada ou com mofo segura água e prejudica as raízes.",
        (
            "Afofe a superfície com cuidado",
            "Troque a terra por um substrato novo e solto",
        ),
    ),
    "nutrient_need": Condition(
        "Pode precisar de adubo",
        "Verde claro por igual em planta bem iluminada pode ser falta de nutrientes.",
        (
            "Na primavera e no verão, use adubo para plantas de casa seguindo a embalagem",
            "Troque a terra se ela não é renovada há mais de um ano",
        ),
    ),
}

CONDITION_ORDER: tuple[str, ...] = tuple(CONDITIONS)
