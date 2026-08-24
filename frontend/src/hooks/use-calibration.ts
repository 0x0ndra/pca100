import { useMutation, useQueryClient } from '@tanstack/react-query'
import { reloadCalibration, revealCalibration } from '@/lib/api'

export function useCalibration() {
  const queryClient = useQueryClient()
  const reload = useMutation({
    mutationFn: reloadCalibration,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['status'] }),
  })
  const reveal = useMutation({ mutationFn: revealCalibration })
  return { reload, reveal }
}
