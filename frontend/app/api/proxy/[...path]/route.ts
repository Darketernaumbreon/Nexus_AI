import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET(
    request: NextRequest,
    context: { params: Promise<{ path: string[] }> }
) {
    try {
        const params = await context.params;
        const path = params.path.join("/");
        const searchParams = request.nextUrl.searchParams.toString();
        const url = `${BACKEND_URL}/api/v1/${path}${searchParams ? `?${searchParams}` : ""}`;

        const response = await fetch(url, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        });

        const data = await response.json();

        return NextResponse.json(data, { status: response.status });
    } catch (error) {
        console.error("API Proxy Error (GET):", error);
        return NextResponse.json(
            { error: "Failed to fetch from backend" },
            { status: 500 }
        );
    }
}

export async function POST(
    request: NextRequest,
    context: { params: Promise<{ path: string[] }> }
) {
    try {
        const params = await context.params;
        const path = params.path.join("/");
        const body = await request.json();
        const url = `${BACKEND_URL}/api/v1/${path}`;

        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(body),
        });

        const data = await response.json();

        return NextResponse.json(data, { status: response.status });
    } catch (error) {
        console.error("API Proxy Error (POST):", error);
        return NextResponse.json(
            { error: "Failed to post to backend" },
            { status: 500 }
        );
    }
}
