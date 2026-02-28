import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { generateQnA, exportQASet } from "@/api/qna";
import type { QASet } from "@/api/types";
import { GenerateForm } from "./GenerateForm";
import { QASetView } from "./QASetView";

export function QnAPage() {
  const [qaSet, setQaSet] = useState<QASet | null>(null);

  const generateMutation = useMutation({
    mutationFn: generateQnA,
    onSuccess: (data) => setQaSet(data),
  });

  const exportMutation = useMutation({
    mutationFn: async ({ format }: { format: "json" | "markdown" }) => {
      if (!qaSet) return;
      const blob = await exportQASet(qaSet.id, { format });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `qa-${qaSet.topic}.${format === "json" ? "json" : "md"}`;
      a.click();
      URL.revokeObjectURL(url);
    },
  });

  if (qaSet) {
    return (
      <QASetView
        qaSet={qaSet}
        onBack={() => setQaSet(null)}
        onExport={(format) => exportMutation.mutate({ format })}
        isExporting={exportMutation.isPending}
      />
    );
  }

  return (
    <GenerateForm
      onGenerate={(data) => generateMutation.mutate(data)}
      isGenerating={generateMutation.isPending}
      error={generateMutation.error?.message}
    />
  );
}
