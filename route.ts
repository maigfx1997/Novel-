import { NextRequest, NextResponse } from "next/server";
import { fetchNovel } from "@/lib/scrapers";

export async function POST(request: NextRequest) {
  try {
    const { url } = await request.json();

    if (!url || typeof url !== "string") {
      return NextResponse.json(
        { error: "URL is required" },
        { status: 400 }
      );
    }

    const novel = await fetchNovel(url.trim());
    return NextResponse.json(novel);
  } catch (error) {
    console.error("Scrape error:", error);
    return NextResponse.json(
      {
        error:
          error instanceof Error
            ? error.message
            : "Failed to fetch novel",
      },
      { status: 500 }
    );
  }
}
