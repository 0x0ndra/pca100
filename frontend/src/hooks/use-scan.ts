import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { captureDark, clearDark, fetchStatus, setAveraging, startScan, stopScan } from '@/lib/api'

const STATUS_QUERY_KEY = ['status']

export function useScan() {
  const queryClient = useQueryClient()
  const invalidateStatus = () => queryClient.invalidateQueries({ queryKey: STATUS_QUERY_KEY })

  const status = useQuery({
    queryKey: STATUS_QUERY_KEY,
    queryFn: fetchStatus,
    refetchInterval: 2000,
  })

  const start = useMutation({ mutationFn: startScan, onSuccess: invalidateStatus })
  const stop = useMutation({ mutationFn: stopScan, onSuccess: invalidateStatus })
  const dark = useMutation({ mutationFn: captureDark, onSuccess: invalidateStatus })
  const clearDarkMutation = useMutation({ mutationFn: clearDark, onSuccess: invalidateStatus })
  const averaging = useMutation({ mutationFn: setAveraging, onSuccess: invalidateStatus })

  return { status, start, stop, dark, clearDark: clearDarkMutation, setAveraging: averaging }
}
