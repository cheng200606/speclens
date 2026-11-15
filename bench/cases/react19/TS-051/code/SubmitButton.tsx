import { useState } from "react";

export function SubmitButton() {
  const [label, setLabel] = useState("Save");

  async function handleSave() {
    setLabel("Saved!");
    await fetch("/api/save", { method: "POST" });
  }

  return <button onClick={handleSave}>{label}</button>;
}
