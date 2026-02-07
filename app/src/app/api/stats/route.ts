import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET() {
  const [totalTerms, approvedTerms, draftTerms, totalProcesses, activeProcesses, categories] =
    await Promise.all([
      prisma.glossaryTerm.count(),
      prisma.glossaryTerm.count({ where: { status: "APPROVED" } }),
      prisma.glossaryTerm.count({ where: { status: "DRAFT" } }),
      prisma.businessProcess.count(),
      prisma.businessProcess.count({ where: { status: "ACTIVE" } }),
      prisma.glossaryTerm.groupBy({ by: ["category"], _count: true }),
    ]);

  return NextResponse.json({
    totalTerms,
    approvedTerms,
    draftTerms,
    totalProcesses,
    activeProcesses,
    categories: categories.filter((c) => c.category),
  });
}
