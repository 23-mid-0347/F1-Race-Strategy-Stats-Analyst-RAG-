import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

export const getHealth = async () => {
  const response = await api.get("/health");
  return response.data;
};

export const getEvents = async (
  season: number,
  limit = 20,
  offset = 0,
) => {
  const response = await api.get("/events", {
    params: {
      season,
      limit,
      offset,
    },
  });

  return response.data;
};

export const getEventResults = async (eventId: number) => {
  const response = await api.get(`/events/${eventId}/results`);
  return response.data;
};

export const getDriverWins = async (season: number) => {
  const response = await api.get("/drivers/wins", {
    params: { season },
  });

  return response.data;
};

export const getDriverCount = async (season: number) => {
  const response = await api.get("/drivers/count", {
    params: { season },
  });

  return response.data;
};

export const getDriverPodiums = async (season: number) => {
  const response = await api.get("/drivers/podiums", {
    params: { season },
  });

  return response.data;
};

export const getConstructorStandings = async (season: number) => {
  const response = await api.get("/constructors/standings", {
    params: { season },
  });

  return response.data;
};

export const getConstructorCount = async (season: number) => {
  const response = await api.get("/constructors/count", {
    params: { season },
  });

  return response.data;
};

export default api;