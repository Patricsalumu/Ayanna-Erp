<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class RestauSalle extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'restau_salles';
    protected $fillable = ['id', 'pos_id', 'nom', 'capacite', 'actif'];
    protected $casts = ['actif' => 'boolean'];

    public function pos()    { return $this->belongsTo(POSPoint::class, 'pos_id'); }
    public function tables() { return $this->hasMany(RestauTable::class, 'salle_id'); }
}
