export interface Property {
  id: number;
  portal: 'mercadolibre' | 'zonaprop' | 'argenprop' | 'properati';
  external_id: string;
  title: string;
  url: string;
  property_type: 'departamento' | 'casa' | 'ph' | 'terreno' | 'otro';
  operation_type: string;
  price_usd: number;
  price_currency_orig?: string;
  price_amount_orig?: number;
  expenses?: number;
  total_area_m2?: number;
  covered_area_m2?: number;
  price_per_m2?: number;
  rooms?: number;
  bedrooms?: number;
  bathrooms?: number;
  garages?: number;
  neighborhood: string;
  zone: string;
  city?: string;
  address?: string;
  latitude?: number;
  longitude?: number;
  description?: string;
  images: string[];
  seller_name?: string;
  seller_type?: string;
  publication_date?: string;
  scraped_at?: string;
  updated_at?: string;
  is_favorite: boolean;
  is_discarded: boolean;
  user_notes?: string;
  cluster_id?: string;
  cluster_confidence?: number;
  duplicates?: Property[];
  best_price_usd?: number;
}

export interface FilterState {
  property_types: string[];
  neighborhoods: string[];
  zones: string[];
  portals: string[];
  min_price?: number;
  max_price?: number;
  min_area?: number;
  max_area?: number;
  min_bedrooms?: number;
  max_bedrooms?: number;
  min_bathrooms?: number;
  days_ago?: number;
  search_query?: string;
  only_favorites: boolean;
  group_duplicates: boolean;
  sort_by: string;
  page: number;
  page_size: number;
}

export interface LocationCatalog {
  [zone: string]: string[];
}

export interface StatsSummary {
  total_properties: number;
  total_favorites: number;
  by_type: Record<string, number>;
  by_portal: Record<string, number>;
  by_zone: Record<string, number>;
}

export interface ScrapeJob {
  id: number;
  portal: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  zone?: string;
  property_type?: string;
  items_found: number;
  items_saved: number;
  message?: string;
  started_at?: string;
  finished_at?: string;
}
