<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class Licence extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'licences';
    protected $fillable = [
        'id', 'enterprise_id', 'licence_key', 'is_active', 'expires_at',
        'max_users', 'max_pos', 'modules_enabled',
    ];
    protected $casts = [
        'is_active' => 'boolean',
        'expires_at' => 'datetime',
        'modules_enabled' => 'array',
    ];

    public function enterprise() { return $this->belongsTo(Entreprise::class, 'enterprise_id'); }
}
