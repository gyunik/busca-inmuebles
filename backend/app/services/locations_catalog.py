import re
import unicodedata

CABA_NEIGHBORHOODS = [
    'Agronomía', 'Almagro', 'Balvanera', 'Barracas', 'Belgrano', 'Boedo', 
    'Caballito', 'Chacarita', 'Coghlan', 'Colegiales', 'Constitución', 'Flores', 
    'Floresta', 'La Boca', 'La Paternal', 'Liniers', 'Mataderos', 'Monte Castro', 
    'Monserrat', 'Nueva Pompeya', 'Núñez', 'Palermo', 'Parque Avellaneda', 
    'Parque Chacabuco', 'Parque Chas', 'Parque Patricios', 'Puerto Madero', 
    'Recoleta', 'Retiro', 'Saavedra', 'San Cristóbal', 'San Nicolás', 'San Telmo', 
    'Vélez Sársfield', 'Versalles', 'Villa Crespo', 'Villa del Parque', 
    'Villa Devoto', 'Villa General Mitre', 'Villa Lugano', 'Villa Luro', 
    'Villa Ortúzar', 'Villa Real', 'Villa Riachuelo', 'Villa Santa Rita', 
    'Villa Soldati', 'Villa Urquiza', 'Villa Pueyrredón'
]

GBA_NORTE_NEIGHBORHOODS = [
    'Vicente López', 'Olivos', 'Florida', 'La Lucila', 'Villa Martelli', 'Munro', 'Carapachay',
    'San Isidro', 'Martínez', 'Acassuso', 'Béccar', 'Boulogne', 'Villa Adelina',
    'San Fernando', 'Victoria', 'Virreyes',
    'Tigre', 'Nordelta', 'Rincón de Milberg', 'Don Torcuato', 'General Pacheco', 'Benavídez',
    'Pilar', 'Del Viso', 'Manzanares', 'Fátima', 'La Lonja',
    'Escobar', 'Belén de Escobar', 'Ingeniero Maschwitz', 'Garín',
    'San Martín', 'Villa Ballester', 'San Andrés', 'José León Suárez'
]

GBA_SUR_NEIGHBORHOODS = [
    'Avellaneda', 'Sarandí', 'Dock Sud', 'Gerli', 'Wilde', 'Piñeyro',
    'Lanús', 'Lanús Este', 'Lanús Oeste', 'Remedios de Escalada', 'Valentín Alsina',
    'Quilmes', 'Bernal', 'Don Bosco', 'Ezpeleta', 'Solano',
    'Lomas de Zamora', 'Banfield', 'Temperley', 'Turdera', 'Llavallol',
    'Almirante Brown', 'Adrogué', 'Burzaco', 'José Mármol', 'Claypole', 'Longchamps',
    'Esteban Echeverría', 'Monte Grande', 'Canning', 'Luis Guillón',
    'Berazategui', 'Hudson', 'Ranelagh', 'Plátanos'
]

GBA_OESTE_NEIGHBORHOODS = [
    'La Matanza', 'Ramos Mejía', 'San Justo', 'Ciudad Evita', 'Villa Luzuriaga', 'Lomas del Mirador', 'Tapiales',
    'Morón', 'Castelar', 'Haedo', 'El Palomar', 'Villa Sarmiento',
    'Tres de Febrero', 'Caseros', 'Ciudad Jardín', 'Santos Lugares', 'Villa Bosch', 'Ciudadela',
    'Ituzaingó', 'Parque Leloir', 'San Antonio de Padua',
    'Hurlingham', 'Villa Tesei', 'William Morris',
    'Moreno', 'Paso del Rey', 'Francisco Álvarez',
    'San Miguel', 'Bella Vista', 'Muñiz'
]

CATALOG_BY_ZONE = {
    'CABA': sorted(CABA_NEIGHBORHOODS),
    'GBA Norte': sorted(GBA_NORTE_NEIGHBORHOODS),
    'GBA Sur': sorted(GBA_SUR_NEIGHBORHOODS),
    'GBA Oeste': sorted(GBA_OESTE_NEIGHBORHOODS)
}

def normalize_text(text: str) -> str:
    if not text:
        return ''
    text = text.lower()
    text = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
    return re.sub(r'[^a-z0-9\s]', ' ', text).strip()

def match_neighborhood(raw_location: str):
    norm_loc = normalize_text(raw_location)
    
    # Direct matching in each zone
    for zone, neighborhoods in CATALOG_BY_ZONE.items():
        for neigh in neighborhoods:
            norm_neigh = normalize_text(neigh)
            # Check exact or boundary contained
            if re.search(r'\b' + re.escape(norm_neigh) + r'\b', norm_loc):
                return neigh, zone
                
    # Check specific subzones like Palermo Soho, Palermo Hollywood, Barrio Norte, etc.
    if 'palermo' in norm_loc:
        return 'Palermo', 'CABA'
    if 'barrio norte' in norm_loc:
        return 'Recoleta', 'CABA'
    if 'belgrano' in norm_loc:
        return 'Belgrano', 'CABA'
    if 'recoleta' in norm_loc:
        return 'Recoleta', 'CABA'
    if 'caballito' in norm_loc:
        return 'Caballito', 'CABA'
    if 'nordelta' in norm_loc:
        return 'Nordelta', 'GBA Norte'
    if 'puerto madero' in norm_loc:
        return 'Puerto Madero', 'CABA'
    if 'las canitas' in norm_loc or 'canitas' in norm_loc:
        return 'Palermo', 'CABA'
    if 'villa crespo' in norm_loc:
        return 'Villa Crespo', 'CABA'
    if 'villa urquiza' in norm_loc:
        return 'Villa Urquiza', 'CABA'
    if 'villa devoto' in norm_loc:
        return 'Villa Devoto', 'CABA'
    if 'almagro' in norm_loc:
        return 'Almagro', 'CABA'
    if 'san telmo' in norm_loc:
        return 'San Telmo', 'CABA'
    if 'vicente lopez' in norm_loc:
        return 'Vicente López', 'GBA Norte'
    if 'olivos' in norm_loc:
        return 'Olivos', 'GBA Norte'
    if 'san isidro' in norm_loc:
        return 'San Isidro', 'GBA Norte'
    if 'tigre' in norm_loc:
        return 'Tigre', 'GBA Norte'
    if 'martinez' in norm_loc:
        return 'Martínez', 'GBA Norte'
    if 'ramos mejia' in norm_loc:
        return 'Ramos Mejía', 'GBA Oeste'
    if 'moron' in norm_loc:
        return 'Morón', 'GBA Oeste'
    if 'castelar' in norm_loc:
        return 'Castelar', 'GBA Oeste'
    if 'lanus' in norm_loc:
        return 'Lanús', 'GBA Sur'
    if 'quilmes' in norm_loc:
        return 'Quilmes', 'GBA Sur'
    if 'lomas de zamora' in norm_loc:
        return 'Lomas de Zamora', 'GBA Sur'
    if 'banfield' in norm_loc:
        return 'Banfield', 'GBA Sur'
    if 'adrogue' in norm_loc:
        return 'Adrogué', 'GBA Sur'
        
    return raw_location.strip() or 'Otro', 'CABA' if 'capital federal' in norm_loc or 'caba' in norm_loc or 'buenos aires' in norm_loc else 'GBA'
