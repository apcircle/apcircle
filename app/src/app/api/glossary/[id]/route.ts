import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const term = await prisma.glossaryTerm.findUnique({
    where: { id },
    include: { processes: { include: { process: true } } },
  });
  if (!term) return NextResponse.json({ error: "Not found" }, { status: 404 });
  return NextResponse.json(term);
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const body = await request.json();
  const term = await prisma.glossaryTerm.update({ where: { id }, data: body });
  return NextResponse.json(term);
}

export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  await prisma.glossaryTerm.delete({ where: { id } });
  return NextResponse.json({ success: true });
}
