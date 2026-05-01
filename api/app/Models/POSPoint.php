<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class POSPoint extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'core_pos_points';
    protected $fillable = ['id', 'enterprise_id', 'module_id', 'name'];

    public function enterprise()    { return $this->belongsTo(Entreprise::class, 'enterprise_id'); }
    public function module()        { return $this->belongsTo(Module::class, 'module_id'); }
    public function comptaConfig()  { return $this->hasOne(ComptaConfig::class, 'pos_id'); }
    public function stockConfig()   { return $this->hasOne(StockConfig::class, 'pos_id'); }
}
