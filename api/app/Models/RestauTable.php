<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class RestauTable extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'restau_tables';
    protected $fillable = ['id', 'salle_id', 'numero', 'nom', 'capacite', 'statut', 'actif'];
    protected $casts = ['actif' => 'boolean'];

    public function salle()   { return $this->belongsTo(RestauSalle::class, 'salle_id'); }
    public function paniers() { return $this->hasMany(RestauPanier::class, 'table_id'); }
}
