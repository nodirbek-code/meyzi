export type Paginated<T> = { count: number; next: string | null; previous: string | null; results: T[] };

export type User = {
  id: number;
  email: string | null;
  email_verified: boolean;
  first_name: string;
  last_name: string;
  full_name: string;
  phone: string | null;
  phone_verified: boolean;
  role: "tourist" | "agency" | "guide" | "business" | "admin";
  language: "uz" | "ru" | "en";
  /** Admin (Django admin paneliga kira oladi) */
  is_staff?: boolean;
};

export type DestinationShort = { id: number; name: string; slug: string };
export type Destination = DestinationShort & {
  region: string;
  short_description: string;
  description?: string;
  cover_image: string | null;
  is_featured: boolean;
  places_count: number;
};

export type Category = { id: number; name: string; slug: string; icon: string; tours_count: number };
export type AgencyShort = {
  id: number;
  name: string;
  slug: string;
  logo: string | null;
  is_verified: boolean;
  is_platform: boolean;
  rating: string;
  reviews_count: number;
};
export type Installment = { months: number; monthly_uzs: number; total_uzs: number };
export type Departure = { id: number; date: string; seats_left: number; price_uzs: number; is_bookable: boolean };

export type TourCard = {
  id: number;
  slug: string;
  title: string;
  short_description: string;
  cover: string | null;
  categories: { name: string; slug: string }[];
  destination: DestinationShort;
  agency: AgencyShort;
  duration_days: number;
  duration_nights: number;
  price_uzs: number;
  installment: Installment;
  next_departure: Departure | null;
  cancellation_policy: "free" | "partial" | "non_refundable";
  rating: string;
  reviews_count: number;
  is_featured: boolean;
};

export type ItineraryItem = {
  start_time: string | null;
  end_time: string | null;
  title: string;
  description: string;
  is_extra_cost: boolean;
};
export type TourDetail = TourCard & {
  description: string;
  max_group_size: number;
  departure_time: string | null;
  return_time: string | null;
  meeting_point: string;
  meeting_latitude: string | null;
  meeting_longitude: string | null;
  meeting_map_url: string;
  price_note: string;
  cancellation_policy_text: string;
  included: string[];
  not_included: string[];
  what_to_bring: string[];
  media: { id: number; kind: "image" | "video"; file: string; caption: string; is_cover: boolean }[];
  itinerary: { day_number: number; title: string; description: string; items: ItineraryItem[] }[];
  departures: Departure[];
  places: string[];
};

export type Review = {
  id: number;
  author: string;
  rating: number;
  text: string;
  agency_reply?: string;
  created_at: string;
  tour_title?: string;
};

export type Booking = {
  code: string;
  status: "pending_payment" | "confirmed" | "cancelled" | "expired" | "completed";
  tour: {
    slug: string;
    title: string;
    duration_days: number;
    meeting_point: string;
    meeting_latitude: string | null;
    meeting_longitude: string | null;
    meeting_map_url: string;
    cover: string | null;
  };
  travelers: { full_name: string; phone: string; birth_date: string | null }[];
  installment: Installment;
  confirmed_at: string | null;
  cancelled_at: string | null;
  cancel_reason: string;
  has_review?: boolean;
  agency: AgencyShort;
  departure_date: string;
  departure_at: string;
  seats: number;
  unit_price_uzs: number;
  total_uzs: number;
  cancellation_policy: string;
  contact_name: string;
  contact_phone: string;
  expires_at: string | null;
  cancelled_by: string;
  refund_uzs: number;
  created_at: string;
};

export type PaymentMethod = {
  code: string;
  name: string;
  description: string;
  logo: string | null;
  enabled: boolean;
  status_text: string;
};
export type Features = {
  languages: { code: string; name: string }[];
  default_language: string;
  ai_route: { enabled: boolean; status_text: string; description: string };
  multilingual_content: { enabled: boolean; status_text: string; description: string };
  payments: PaymentMethod[];
};

export type ArticleCard = {
  id: number;
  title: string;
  slug: string;
  excerpt: string;
  cover: string | null;
  destination: DestinationShort | null;
  published_at: string;
};
export type Article = ArticleCard & { body: string; tours: TourCard[] };
export type Faq = { id: number; question: string; answer: string };
export type Page = { slug: string; title: string; body: string; updated_at: string };

export type GuideCard = {
  id: number;
  slug: string;
  display_name: string;
  photo: string | null;
  languages: string[];
  specializations: string[];
  destinations: DestinationShort[];
  experience_years: number;
  is_certified: boolean;
  price_half_day_uzs: number;
  price_full_day_uzs: number;
  price_per_day_uzs: number;
  rating: string;
  reviews_count: number;
};
export type MeetingPoint = {
  id: number;
  destination: string;
  name: string;
  address: string;
  latitude: string;
  longitude: string;
};
export type GuideDetail = GuideCard & {
  bio: string;
  group_surcharge_percent: number;
  max_group_size: number;
  meeting_points: MeetingPoint[];
};
export type GuideQuote = { duration: string; days: number; group_size: number; unit_price_uzs: number; base_uzs: number; surcharge_uzs: number; total_uzs: number };

export type HotelCard = {
  id: number;
  slug: string;
  name: string;
  kind: "hotel" | "hostel" | "guesthouse" | "resort";
  stars: number | null;
  destination: DestinationShort;
  address: string;
  cover: string | null;
  amenities: string[];
  min_price_uzs: number | null;
  cancellation_policy: string;
  rating: string;
  reviews_count: number;
};
export type HotelDetail = HotelCard & {
  description: string;
  latitude: string | null;
  longitude: string | null;
  check_in_time: string;
  check_out_time: string;
  cancellation_policy_text: string;
  images: { id: number; kind: "image" | "video"; image: string; caption: string }[];
};
export type RoomOffer = {
  id: number;
  name: string;
  description: string;
  capacity: number;
  beds: string;
  size_m2: number | null;
  price_per_night_uzs: number;
  amenities: string[];
  image: string | null;
  available_rooms: number | null;
  nights: number | null;
  stay_total_uzs: number | null;
};
