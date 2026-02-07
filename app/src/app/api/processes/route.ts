import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const search = searchParams.get("search") || "";
  const status = searchParams.get("status") || "";
  const department = searchParams.get("department") || "";

  const where: Record<string, unknown> = {};

  if (search) {
    where.OR = [
      { name: { contains: search, mode: "insensitive" } },
      { description: { contains: search, mode: "insensitive" } },
    ];
  }
  if (status) where.status = status;
  if (department) where.department = department;

  const processes = await prisma.businessProcess.findMany({
    where,
    orderBy: { name: "asc" },
    include: {
      glossaryTerms: { include: { term: true } },
      children: true,
    },
  });

  return NextResponse.json(processes);
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { glossaryTermIds, ...data } = body;

  const process = await prisma.businessProcess.create({
    data: {
      ...data,
      glossaryTerms: glossaryTermIds
        ? {
            create: glossaryTermIds.map((termId: string) => ({ termId })),
          }
        : undefined,
    },
    include: { glossaryTerms: { include: { term: true } } },
  });

  return NextResponse.json(process, { status: 201 });
}
