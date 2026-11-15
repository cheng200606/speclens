import { useOptimistic, startTransition } from "react";

export function SubmitButton() {
  const [label, setLabel] = useOptimistic("Save");

  async function handleSave() {
    startTransition(async () => {
      setLabel("Saved!");
      await fetch("/api/save", { method: "POST" });
    });
  }

  return <button onClick={handleSave}>{label}</button>;
}
