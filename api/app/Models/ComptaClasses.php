<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class ComptaClasses extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'compta_classes';
    protected $fillable = ['id', 'code', 'nom', 'libelle', 'type', 'document', 'enterprise_id', 'actif'];
    protected $casts = ['actif' => 'boolean'];

    public function comptes()    { return $this->hasMany(ComptaComptes::class, 'classe_comptable_id'); }
    public function enterprise() { return $this->belongsTo(Entreprise::class, 'enterprise_id'); }
}
