import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const search = searchParams.get("search") || "";
  const category = searchParams.get("category") || "";
  const status = searchParams.get("status") || "";

  const where: Record<string, unknown> = {};

  if (search) {
    where.OR = [
      { term: { contains: search, mode: "insensitive" } },
      { definition: { contains: search, mode: "insensitive" } },
    ];
  }
  if (category) where.category = category;
  if (status) where.status = status;

  const terms = await prisma.glossaryTerm.findMany({
    where,
    orderBy: { term: "asc" },
    include: { processes: { include: { process: true } } },
  });

  return NextResponse.json(terms);
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  const term = await prisma.glossaryTerm.create({ data: body });
  return NextResponse.json(term, { status: 201 });
}
