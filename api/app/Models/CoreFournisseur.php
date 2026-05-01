<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class CoreFournisseur extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'core_fournisseurs';
    protected $fillable = ['id', 'nom', 'telephone', 'adresse', 'email'];

    public function commandes() { return $this->hasMany(AchatCommande::class, 'fournisseur_id'); }
}
