<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class AchatDepense extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'achat_depenses';
    protected $fillable = ['id', 'bon_commande_id', 'montant', 'mode_paiement', 'description', 'date_paiement', 'reference'];
    protected $casts = ['montant' => 'decimal:2', 'date_paiement' => 'datetime'];

    public function commande() { return $this->belongsTo(AchatCommande::class, 'bon_commande_id'); }
}
