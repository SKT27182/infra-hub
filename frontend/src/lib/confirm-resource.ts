export function confirmResourceDeletion(kind: string, name: string): boolean {
  const entered = window.prompt(
    `Deleting ${kind} "${name}" is irreversible. Type the exact name to continue:`
  )
  return entered === name
}
