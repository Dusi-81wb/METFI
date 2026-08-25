import { HealthResponse } from "../types";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchHealthStatus(): Promise<HealthResponse> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/health`, {
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
    });

    if (!res.ok) {
      throw new Error(`Health check failed with status: ${res.status}`);
    }

    return await res.json();
  } catch (error) {
    console.error("Failed to connect to METFI backend:", error);
    throw error;
  }
}
