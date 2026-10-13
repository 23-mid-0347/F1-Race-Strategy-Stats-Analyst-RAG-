import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

// ─── Types ────────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string;
  database: string;
}

export interface ConstructorStanding {
  name: string;
  total_points: number;
}

export interface DriverWin {
  full_name: string;
  wins: number;
}

export interface DriverPodium {
  full_name: string;
  podiums: number;
}

export interface EventSummary {
  event_id: number;
  season: number;
  round: number;
  event_name: string;
  circuit_name: string | null;
  event_date: string | null;
}

export interface PaginatedEvents {
  total: number;
  limit: number;
  offset: number;
  items: EventSummary[];
}

export interface RaceResultRow {
  finish_position: number | null;
  grid_position: number | null;
  driver_code: string;
  full_name: string;
  constructor_name: string | null;
  points: number;
  status: string | null;
}

export interface EventResults {
  event_id: number;
  event_name: string;
  season: number;
  round: number;
  results: RaceResultRow[];
}

export interface DriverDetail {
  driver_id: number;
  driver_code: string;
  full_name: string;
  nationality: string | null;
  date_of_birth: string | null;
}

export interface DriverStats {
  driver_id: number;
  full_name: string;
  season: number | null;
  races: number;
  wins: number;
  podiums: number;
  poles: number;
  dnfs: number;
  avg_finish: number | null;
}

// ─── API calls ────────────────────────────────────────────────────────────────

export const getHealth = async (): Promise<HealthResponse> => {
  const response = await api.get<HealthResponse>("/health");
  return response.data;
};

export const getEvents = async (
  season?: number,
  limit = 20,
  offset = 0,
): Promise<PaginatedEvents> => {
  const response = await api.get<PaginatedEvents>("/events", {
    params: { ...(season !== undefined && { season }), limit, offset },
  });
  return response.data;
};

export const getEventResults = async (eventId: number): Promise<EventResults> => {
  const response = await api.get<EventResults>(`/events/${eventId}/results`);
  return response.data;
};

export const getDriverWins = async (season?: number): Promise<DriverWin[]> => {
  const response = await api.get<DriverWin[]>("/drivers/wins", {
    params: season !== undefined ? { season } : {},
  });
  return response.data;
};

export const getDriverPodiums = async (season?: number): Promise<DriverPodium[]> => {
  const response = await api.get<DriverPodium[]>("/drivers/podiums", {
    params: season !== undefined ? { season } : {},
  });
  return response.data;
};

export const getDriverCount = async (season?: number): Promise<{ count: number }> => {
  const response = await api.get<{ count: number }>("/drivers/count", {
    params: season !== undefined ? { season } : {},
  });
  return response.data;
};

export const getDriver = async (driverId: number): Promise<DriverDetail> => {
  const response = await api.get<DriverDetail>(`/drivers/${driverId}`);
  return response.data;
};

export const getDriverStats = async (
  driverId: number,
  season?: number,
): Promise<DriverStats> => {
  const response = await api.get<DriverStats>(`/drivers/${driverId}/stats`, {
    params: season !== undefined ? { season } : {},
  });
  return response.data;
};

export const getConstructorStandings = async (
  season?: number,
): Promise<ConstructorStanding[]> => {
  const response = await api.get<ConstructorStanding[]>("/constructors/standings", {
    params: season !== undefined ? { season } : {},
  });
  return response.data;
};

export const getConstructorCount = async (season?: number): Promise<{ count: number }> => {
  const response = await api.get<{ count: number }>("/constructors/count", {
    params: season !== undefined ? { season } : {},
  });
  return response.data;
};

export const getFastestLap = async (sessionId: number) => {
  const response = await api.get(`/sessions/${sessionId}/fastest-lap`);
  return response.data;
};

export default api;