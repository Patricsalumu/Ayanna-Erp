<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Services\SyncService;
use Carbon\Carbon;
use Illuminate\Http\Request;

class SyncController extends Controller
{
    public function __construct(protected SyncService $syncService) {}

    /**
     * POST /api/sync/push
     *
     * Body:
     * {
     *   "operations": [
     *     {
     *       "table": "core_products",
     *       "operation": "INSERT|UPDATE|DELETE",
     *       "data": { "id": "<uuid>", ... },
     *       "client_updated_at": "2024-01-15T10:30:00Z"
     *     }
     *   ]
     * }
     */
    public function push(Request $request)
    {
        $request->validate([
            'operations'                   => 'required|array|min:1',
            'operations.*.table'           => 'required|string',
            'operations.*.operation'       => 'required|string|in:INSERT,UPDATE,DELETE',
            'operations.*.data'            => 'required|array',
            'operations.*.data.id'         => 'required|string',
            'operations.*.client_updated_at' => 'nullable|date',
        ]);

        $result = $this->syncService->push(
            $request->input('operations'),
            $request->user()->id
        );

        $status = empty($result['errors']) ? 200 : 207; // 207 Multi-Status if partial failure
        return response()->json($result, $status);
    }

    /**
     * GET /api/sync/pull?last_sync=ISO8601
     *
     * Returns all records created/updated/deleted after last_sync.
     * If last_sync is omitted, returns everything (full sync).
     */
    public function pull(Request $request)
    {
        $request->validate([
            'last_sync' => 'nullable|date',
        ]);

        $lastSync = $request->filled('last_sync')
            ? Carbon::parse($request->input('last_sync'))
            : Carbon::createFromTimestamp(0);

        $data = $this->syncService->pull($lastSync);

        return response()->json([
            'server_time' => now()->toIso8601String(),
            'data'        => $data,
        ]);
    }
}
