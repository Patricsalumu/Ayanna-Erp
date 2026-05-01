<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class AchatCommandeLigne extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'achat_commande_lignes';
    protected $fillable = ['id', 'bon_commande_id', 'produit_id', 'quantite', 'prix_unitaire', 'remise_ligne', 'total_ligne'];
    protected $casts = ['quantite' => 'decimal:2', 'prix_unitaire' => 'decimal:2', 'remise_ligne' => 'decimal:2', 'total_ligne' => 'decimal:2'];

    public function commande() { return $this->belongsTo(AchatCommande::class, 'bon_commande_id'); }
    public function produit()  { return $this->belongsTo(CoreProduct::class, 'produit_id'); }
}
