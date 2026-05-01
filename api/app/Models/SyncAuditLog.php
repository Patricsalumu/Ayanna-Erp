<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class SyncAuditLog extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'sync_audit_logs';
    protected $fillable = [
        'id', 'table_name', 'record_id', 'operation',
        'client_data', 'server_data_before', 'conflict_resolved',
        'client_updated_at', 'synced_by',
    ];
    protected $casts = [
        'client_data' => 'array',
        'server_data_before' => 'array',
        'conflict_resolved' => 'boolean',
        'client_updated_at' => 'datetime',
    ];

    public function syncedBy() { return $this->belongsTo(User::class, 'synced_by'); }
}
