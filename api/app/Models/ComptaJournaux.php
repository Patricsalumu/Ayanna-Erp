<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class ComptaJournaux extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'compta_journaux';
    protected $fillable = [
        'id', 'date_operation', 'libelle', 'montant', 'type_operation',
        'reference', 'description', 'enterprise_id', 'user_id',
        'valide', 'valide_by', 'date_validation',
    ];
    protected $casts = [
        'valide'          => 'boolean',
        'montant'         => 'decimal:2',
        'date_operation'  => 'datetime',
        'date_validation' => 'datetime',
    ];

    public function enterprise() { return $this->belongsTo(Entreprise::class, 'enterprise_id'); }
    public function user()       { return $this->belongsTo(User::class, 'user_id'); }
    public function ecritures()  { return $this->hasMany(ComptaEcritures::class, 'journal_id'); }
}
