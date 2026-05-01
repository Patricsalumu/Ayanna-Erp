<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class ComptaComptes extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'compta_comptes';
    protected $fillable = ['id', 'numero', 'nom', 'libelle', 'actif', 'is_default', 'classe_comptable_id'];
    protected $casts = ['actif' => 'boolean', 'is_default' => 'boolean'];

    public function classeComptable() { return $this->belongsTo(ComptaClasses::class, 'classe_comptable_id'); }
    public function ecritures()       { return $this->hasMany(ComptaEcritures::class, 'compte_comptable_id'); }
}
