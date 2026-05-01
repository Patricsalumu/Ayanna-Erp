<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class Module extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'modules';
    protected $fillable = ['id', 'name', 'description'];
    public function posPoints() { return $this->hasMany(POSPoint::class, 'module_id'); }
}
