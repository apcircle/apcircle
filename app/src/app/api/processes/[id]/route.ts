import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const process = await prisma.businessProcess.findUnique({
    where: { id },
    include: {
      glossaryTerms: { include: { term: true } },
      children: true,
      parent: true,
    },
  });
  if (!process)
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  return NextResponse.json(process);
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const body = await request.json();
  const { glossaryTermIds, ...data } = body;

  if (glossaryTermIds) {
    await prisma.processGlossaryTerm.deleteMany({ where: { processId: id } });
  }

  const process = await prisma.businessProcess.update({
    where: { id },
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

  return NextResponse.json(process);
}

export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  await prisma.businessProcess.delete({ where: { id } });
  return NextResponse.json({ success: true });
}
